# LicenSense

## Codebook
The codebook cited in Section V.B is shown in Codebook.pdf

## Final Result
The ```Final Result.pdf``` contains the detection results of the violation detection.

The detailed result is maintained on [Google Drive](https://drive.google.com/drive/folders/1FarX8QCUYbcvTaLdkSCsM8FMvpZWX1U5?usp=sharing).

Inside the folder ```LNCD-Agent/scripts```, it has the script to analyze the results maintained on [Google Drive](https://drive.google.com/drive/folders/1FarX8QCUYbcvTaLdkSCsM8FMvpZWX1U5?usp=sharing) to generate the ```Final Result.pdf```.

## LNCD-Agent
Inside the ```LNCD-Agent``` folder, it maintains the source code of LNCD-Agent.

By running ```langgraph dev``` inside the folder, it will shows the ```LangSmith``` UI for the agent.

**Important Notice**: To reproduce our whole experiment, it may cost around 2k-3k dollars. To reproduce the result, it is expected to use the scripts and our existed result on Google Drive.

***Example Usage:***
```
# Representative Term is the representative term for the paper, which can represent the paper in searching
RepresentativeTerm: BRSET

# Title is the paper/dataset original title
Title: A Brazilian Multilabel Ophthalmological Dataset (BRSET)

# Website is the website contains the DOI of the paper/dataset
Website: https://doi.org/10.13026/1pht-2b69

# Keywords of the dataset
Keywords: Medical Dataset

# Description of the dataset
Description: The Brazilian Multilabel Ophthalmological Dataset (BRSET) is a multi-labeled ophthalmological dataset designed to improve scientific community development and validate machine learning models. In ophthalmology, ancillary exams support medical decisions and can be used to develop algorithms; however, the availability and representativeness of ophthalmological datasets are limited. This dataset consists of 16,266 images from 8,524 Brazilian patients. Demographics, macula, optic disc, and vessels anatomical parameters, focus, illumination, image field, and artifacts as quality control, and multi-labels are included alongside color fundus retinal photos. This dataset enables computer vision models to predict demographic characteristics and multi-label disease classification using retinal fundus photos.

# Paper citation that can be searched in Google Scholar
Citation: A Brazilian Multilabel Ophthalmological Dataset (BRSET)

# License of the dataset: it can the license name (e.g. CC-BY-NC-ND-4.0), license website, all text version of license
License: https://physionet.org/content/brazilian-ophthalmological/view-license/1.0.1/
```
