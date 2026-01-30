# MIRACLE SDK 🫀

**The Official Python SDK for the MIRACLE API**

[![PyPI version](https://badge.fury.io/py/miracle-sdk.svg)](https://pypi.org/project/miracle-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

📦 **PyPI**: [pypi.org/project/miracle-sdk](https://pypi.org/project/miracle-sdk/)

---

> **MIRACLE**: **M**R **I**maging **R**eference **A**PI for **C**ardiovascular **L**imits from **E**vidence

The MIRACLE SDK provides a simple, typed, and high-performance Python interface to access standardized cardiovascular MRI reference values. Built for data scientists and medical researchers who need to process cardiac imaging data at scale.

## ✨ Features

- **34 Endpoints**: Access all MIRACLE API domains with auto-generated, typed methods.
- **Batch Processing**: Process hundreds of patients in parallel with `MiracleBatch`.
- **IDE Support**: Full autocomplete and type hints for VS Code, PyCharm, and more.
- **Battle-Tested**: Verified with stress tests (16+ concurrent requests, 100% success rate).

---

## 🚀 Installation

```bash
pip install miracle-sdk
```

---

## 📖 Quick Start

### Single Request

```python
from miracle import Miracle

# Initialize the client
client = Miracle()

# Get reference values for a pediatric left ventricle
result = client.pediatric_ventricle_reference_values(
    parameter="LVEDV",
    gender="Male",
    measured=62.5,
    ht_cm=110,
    wt_kg=22
)

print(result)
# {'inputs': {...}, 'results': {'calc_z': 0.5, 'calc_percentile': 69.1, ...}}
```

### Batch Processing

Process an entire CSV of patients with multi-threaded parallelism.

**Input CSV (`patients.csv`):**
```csv
patient_id,gender,height_cm,weight_kg,lv_volume,param_type
001,Male,120,30,75,LVEDV
002,Female,110,25,60,LVEDV
```

**Code:**
```python
from miracle import MiracleBatch

# Initialize the batch processor
processor = MiracleBatch(max_workers=10)

# Define how your CSV columns map to API parameters
mapping = {
    "gender": "gender",
    "ht_cm": "height_cm",
    "wt_kg": "weight_kg",
    "measured": "lv_volume",
    "parameter": "param_type"
}

# Process the CSV
df_results = processor.process_csv(
    file_path="patients.csv",
    domain="Pediatric_Ventricle",
    mapping=mapping
)

# Save the enriched data
df_results.to_csv("patients_with_zscores.csv", index=False)
```

> [!TIP]
> **Performance**: In stress tests, the SDK processed **16 concurrent requests in ~7.5 seconds** with a 100% success rate.

---

## 🗺️ Parameter Mapping Guide

The `mapping` dictionary connects your **CSV column names** to the **API parameter names**.

```python
mapping = {
    "API_PARAMETER": "YOUR_CSV_COLUMN",
    "ht_cm": "Patient_Height",  # Example
}
```

### How to Find API Parameters

1.  **Online Docs**: Visit [miracleapi.readme.io](https://miracleapi.readme.io/) and check the "Query Parameters" for your endpoint.
2.  **Python Help**: Use the built-in docstrings:
    ```python
    help(client.lv_reference_values)
    ```

### Common Parameters

| Parameter   | Type   | Description                                      |
|-------------|--------|--------------------------------------------------|
| `gender`    | `str`  | `"Male"` or `"Female"`                           |
| `age`       | `float`| Patient age in years                             |
| `ht_cm`     | `float`| Height in centimeters                            |
| `wt_kg`     | `float`| Weight in kilograms                              |
| `measured`  | `float`| The measured value (e.g., volume, diameter)      |
| `parameter` | `str`  | The measurement type (e.g., `"LVEDV"`, `"LVEF"`) |

> [!IMPORTANT]
> The `parameter` field is **required** for most domains.

---

## 🏗️ Architecture

This SDK is **auto-generated** from the official [OpenAPI specifications](https://miracleapi.readme.io/). This guarantees:

- **Consistency**: Python methods always match the live API.
- **Type Safety**: Full autocomplete and type hints.
- **Reliability**: API changes are automatically reflected in the SDK.

---

## 🤝 Contributing

Contributions are welcome! Please see the [main MIRACLE-API repository](https://github.com/drankush/MIRACLE-API) for the source of truth.

**Development Setup:**
```bash
git clone https://github.com/drankush/MIRACLE-sdk.git
cd MIRACLE-sdk
pip install -e .[dev]
```

**Regenerate the client from OpenAPI specs:**
```bash
python scripts/generate.py
```

---

## 📖 Citation

If you use this SDK in your research, please cite:

> **MIRACLE: MR Imaging Reference API for Cardiovascular Limits from Evidence**
> *Authors: Ankush et al.*
> Journal of Cardiovascular Magnetic Resonance (2026)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for the Cardiac Imaging Research Community
</p>
