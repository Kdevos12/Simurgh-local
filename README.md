# Simurgh-local
Simurgh is a local ChEMBL molecule retriever that lets you search for compounds based on mode of action and clinical phase. Super handy for quickly finding relevant molecules.
<img src="https://github.com/user-attachments/assets/d934f671-8336-4a19-bd93-7fb7fb79e106" alt="Capture d’écran_2025-06-28_14-22-25" width="50%">

Search results are saved as CSV files. You can find them in the right-hand menu on the main page. Clicking on a file opens a dedicated visualization page.

![Capture d’écran_2025-06-28_14-12-07](https://github.com/user-attachments/assets/816f86da-ab7e-4173-aab7-dc94a7ee9ca3)

This page also includes several tools to help you predict various properties of a selected molecule, using its SMILES code.

Integrated Tools (via iFrame):
SwissADME -  For ADME (Absorption, Distribution, Metabolism, Excretion) predictions. [http://www.swissadme.ch/]

SwissTargetPrediction -  To predict likely biological targets of your compound.  [http://www.swisstargetprediction.ch/]

LightBBB -  For blood-brain barrier (BBB) permeability prediction. [https://academic.oup.com/bioinformatics/article/37/8/1135/5942084]

ProTox-3.0 - To assess toxicity across various biological endpoints.  [https://pubmed.ncbi.nlm.nih.gov/38647086/] 

---

## Installation

Simurgh is pretty easy to install , the only requirement is to have Conda installed.

1.  create the environment using the provided `environment.yml` file:

   ```bash
   conda env create -f environment.yml
   ```

2. Next, activate the environment and run the app:

   ```bash
   conda activate simurgh  
   python3 app.py
   ```

3. Finally, click on the `localhost` address shown in your terminal, and you’re good to go !


<img src="https://github.com/user-attachments/assets/3c4ef552-ce26-4cb6-ae84-04a887da30b0" alt="46f18edf044ba5d81976802ae1c07b8f" width="33%">
