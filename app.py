import pandas as pd
import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, flash


from chembl_webresource_client.settings import Settings
Settings.Instance().cache_backend = 'memory'
Settings.Instance().cache_enabled = True 

from chembl_webresource_client.new_client import new_client

app = Flask(__name__)
app.secret_key = ''
UPLOAD_FOLDER = 'csv_files' 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0

def fetch_molecules(
    target_id: str,
    min_phase: int = 1,
    action_type: str = None,
    save_csv: bool = True
) -> pd.DataFrame:

    mech = new_client.mechanism
    mol  = new_client.molecule
    drug = new_client.drug
    rows = []

    mech_filters = {"target_chembl_id": target_id}
    if action_type and action_type != "ALL":
        mech_filters["action_type"] = action_type

    query_limit = 1000 
    count = 0

    try:
        for m in mech.filter(**mech_filters):
            if count >= query_limit:
                flash(f"The limit of {query_limit} molecules got reached for  '{target_id}'. Le retrieval stopped", 'warning')
                break

            mol_id = m["molecule_chembl_id"]
            rec = mol.get(mol_id)
            if not rec:
                continue

            phase = num(rec.get("max_phase"))
            if min_phase > 0 and phase < min_phase:
                continue

            struct = (rec.get("molecule_structures") or {}).get("canonical_smiles")
            
            try:
                d = drug.filter(molecule_chembl_id=mol_id)
                dose = d[0].get("max_single_dose") if d else None
            except Exception:
                dose = None

            rows.append({
                "chembl_id":    mol_id,
                "name":         rec.get("pref_name") or mol_id,
                "max_phase":    phase,
                "smiles":       struct,
                "typical_dose": dose,
            })
            count += 1

    except Exception as e:
        flash(f"Error while retrieving chembl data for '{target_id}': {e}", 'error')
        return pd.DataFrame()

    df = pd.DataFrame(rows).drop_duplicates("chembl_id") \
                           .sort_values("max_phase", ascending=False)

    if save_csv:
        at = action_type if action_type and action_type != "ALL" else "ALL"
        ph = f"phase{min_phase}plus" if min_phase > 0 else "all"
        fn = os.path.join(app.config['UPLOAD_FOLDER'], f"{target_id.lower()}_{at.lower()}_{ph}.csv")
        df.to_csv(fn, index=False)
        flash(f"File saved : '{fn}' with {len(df)} entries.", 'success')

    return df

action_types = [
    "ALL",
    "AGONIST", "ANTAGONIST", "INHIBITOR", "BLOCKER", "PARTIAL AGONIST",
    "INVERSE AGONIST", "MODULATOR", "ACTIVATOR", "SUPPRESSOR", "INDUCER",
    "STIMULATOR", "POSITIVE ALLOSTERIC MODULATOR",
    "NEGATIVE ALLOSTERIC MODULATOR", "OPENER", "CLOSER", "PARTIAL ANTAGONIST",
    "INHIBITOR, UNCOMPETITIVE", "INHIBITOR, COMPETITIVE",
    "INHIBITOR, NONCOMPETITIVE", "INHIBITOR, ALLOSTERIC", "INHIBITOR, MIXED",
    "INHIBITOR, SUICIDE", "INHIBITOR, TRANSITION STATE",
    "INHIBITOR, MECHANISM-BASED", "INHIBITOR, REVERSIBLE",
    "INHIBITOR, IRREVERSIBLE", "ANTAGONIST, COMPETITIVE",
    "ANTAGONIST, NONCOMPETITIVE", "ANTAGONIST, ALLOSTERIC", "AGONIST, PARTIAL",
    "AGONIST, FULL", "AGONIST, ALLOSTERIC"
]


def list_csv_files():
    """
    Returns a list of CSV file names present in the UPLOAD_FOLDER.
    """
    csv_files = []
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if filename.endswith('.csv'):
                csv_files.append(filename)
    except FileNotFoundError:
        pass
    return sorted(csv_files)


@app.route('/')
def index():
    """
    Displays the home page with the configuration form and the list of CSV files.
    """
    csv_files = list_csv_files()
    return render_template('index.html', csv_files=csv_files, action_types=action_types)

@app.route('/fetch_and_save_molecules', methods=['POST'])
def fetch_and_save_molecules_route():
    """
    Retrieves form parameters, calls fetch_molecules, and handles flash messages.
    """
    target_id = request.form.get('target_id')
    min_phase_str = request.form.get('min_phase')
    action_type = request.form.get('action_type')

    if not target_id or " " in target_id:
        flash('Target ID is required/There is an error in target ID', 'error')
        return redirect(url_for('index'))

    try:
        min_phase = int(min_phase_str)
        if not (0 <= min_phase <= 5):
            flash('Minimal phase must be between 0 & 4 ', 'error')
            return redirect(url_for('index'))
    except ValueError:
        flash('The minimal phase must be an integer :.', 'error')
        return redirect(url_for('index'))
    
    actual_action_type = None if action_type == "ALL" else action_type

    try:
        fetch_molecules(
            target_id=target_id,
            min_phase=min_phase,
            action_type=actual_action_type,
            save_csv=True
        )
    except Exception as e:
        flash(f"unexpected error during molecule retrieval : {e}- it is possible that no molecule matches your query, verify the ID.", 'error')

    return redirect(url_for('index'))

@app.route('/view_csv/<filename>')
def view_csv(filename):
    """
    Displays the content of a specific CSV file in a table.
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        flash(f"The file '{filename}' doesn't exist ", 'error')
        return redirect(url_for('index'))

    try:

        df = pd.read_csv(filepath, low_memory=False)

        df_records = df.to_dict(orient='records')
        column_names = df.columns.tolist() 

        return render_template('view_csv.html', 
                               filename=filename, 
                               column_names=column_names,
                               data_rows=df_records)
    except pd.errors.EmptyDataError:
        flash(f"The file '{filename}' is empty or badly formated", 'warning')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Erro while reading'{filename}' : {e}", 'error')
        return redirect(url_for('index'))

@app.route('/download_csv/<filename>')
def download_csv(filename):
    """
    Allows downloading a specific CSV file from the 'csv_files' folder.
    """
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except FileNotFoundError:
        flash(f"The file '{filename}' was not found.", 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"An error occurred during file download: {e}", 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
