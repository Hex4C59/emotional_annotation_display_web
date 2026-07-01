# CCSEMO Dataset and Annotation Resources

This repository provides code archives and supporting materials for CCSEMO, a Chinese counseling speech emotion dataset and annotation framework.

CCSEMO focuses on real-world counseling conversations, where emotional expressions are often subtle, natural, and context-dependent. The resources in this repository support dataset annotation, annotation-system deployment, and baseline speech emotion recognition experiments.

## Repository Contents

### Annotation System Archives

- `CCSEMO_Official_Annotation_System_Code.zip`

  Official annotation system code used for the CCSEMO annotation workflow. It contains the formal annotation platform for speech segment labeling, annotator testing, management, and quality-control related functions.

- `CCSEMO_Experimental_Annotation.zip`

  Experimental annotation system code and related materials. This archive contains the earlier experimental annotation implementation and supporting files.

### Baseline Experiment Archives

- `CCSEMO_Continuous_Emotion_Recognition_Baseline.zip`

  Baseline code for continuous emotion recognition experiments, including Valence-Arousal prediction with pretrained speech models and pitch feature fusion.

- `CCSEMO_Discrete_Emotion_Recognition_Baseline.zip`

  Baseline code for discrete emotion classification experiments, including 4-class and 7-class speech emotion recognition.

### License Agreement

- `License Agreement_CCSEMO_SIAT.docx`

  Non-exclusive license agreement template for requesting access to the CCSEMO dataset. The dataset is released for research purposes only.

## Dataset Access

Researchers who request access to the CCSEMO dataset should complete and sign the license agreement before receiving the data.

Completed license agreements and dataset access requests can be sent to:

```text
huanraozhineng2@siat.ac.cn
```

The signed agreement should include the applicant's name, title, institution, address, email, handwritten signature, and date.

The dataset must not be used for commercial purposes, redistributed, published, copied, sublicensed, or made available to third parties without prior written consent from AIMSL, SIAT.

## Associated Publication

This repository accompanies the work described in the following paper:

**CCSEMO: A Chinese Counseling Speech Emotion Dataset annotated via a unified standardized annotation framework**

The paper presents the CCSEMO dataset, a standardized annotation framework for Chinese counseling speech emotion data, and the balanced CCSEMO-mini subset.

## Interface Preview

The annotation system provides two task-specific interfaces: a discrete emotion annotation page for categorical emotion labels, and a continuous emotion annotation page for Valence-Arousal annotation.

### Discrete Emotion Annotation Interface

![Discrete emotion annotation interface](images/discrete-emotion-annotation-interface.png)

### Continuous Emotion Annotation Interface

![Continuous emotion annotation interface](images/continuous-emotion-annotation-interface.png)

## Citation

If you use CCSEMO or the related resources in this repository, please cite:

```bibtex
@article{guo2026ccsemo,
  title={CCSEMO: A Chinese Counseling Speech Emotion Dataset annotated via a unified standardized annotation framework},
  author={Guo, Zhixing and Liu, Yang and Yang, Yudong and Yu, Hangbin and Su, Rongfeng and Yan, Nan and Wang, Lan},
  journal={Pattern Recognition},
  pages={114277},
  year={2026},
  publisher={Elsevier}
}
```
