# A/B Testing & Conversion Analyzer

A data analytics project for evaluating A/B experiments, comparing conversion rates, and interpreting whether a treatment performs differently from a control group.

The project includes a Jupyter Notebook for detailed analysis and a Streamlit app for an interactive dashboard.

Streamlit: https://ab-testing-conversion-analyzer.streamlit.app/

## Project Features

### Jupyter Notebook
- Data cleaning and validation
- Data cleaning log showing rows before and after cleaning steps
- Sample Ratio Mismatch (SRM) check
- Control and treatment conversion-rate analysis
- Absolute and relative lift
- Two-proportion z-test for statistical significance
- 95% confidence interval for the difference in conversion rates
- Statistical power and sample-size planning
- Written conclusion with business interpretation

### Streamlit Dashboard
- Upload an experiment CSV
- Validate required columns and clean invalid records
- Compare control and treatment conversion rates
- View user counts, conversions, and conversion rates
- View relative lift, p-value, and confidence interval
- Visualize conversion rates with a chart

> Note: The notebook and Streamlit app are separate interfaces. Features implemented in the notebook do not automatically appear in the Streamlit dashboard. Add them to the app separately if you want them available on the website.

## Tech Stack

- Python
- Pandas
- NumPy
- SciPy
- Statsmodels
- Streamlit
- Jupyter Notebook

## Repository Structure

```text
ab-testing-conversion-analyzer/
├── ab_testing_analysis.ipynb
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

Your filenames may differ. Update the commands below if your files use different names.

## Dataset Format

The Streamlit app expects a CSV containing these columns:

| Column | Description | Example values |
|---|---|---|
| `group` | Experiment group | `control`, `treatment` |
| `converted` | Whether the user converted | `0`, `1` |

Example:

```csv
group,converted
control,0
control,1
treatment,1
treatment,0
```

Use one row per randomized unit (usually one user) for a standard user-level conversion analysis. If your dataset contains repeated rows per user, deduplicate or aggregate it according to the experiment's unit of randomization before analyzing it.

The notebook may also use columns such as `user_id` and `landing_page`, depending on the dataset and cleaning workflow.

## Installation

### 1. Clone the repository

Replace `YOUR_USERNAME` with your GitHub username and `YOUR_REPOSITORY` with the repository name.

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd YOUR_REPOSITORY
```

### 2. Create a virtual environment (recommended)

Windows:

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you do not have a `requirements.txt` file yet, create one containing:

```text
streamlit
pandas
numpy
scipy
statsmodels
jupyter
```

## Run the Streamlit App

From the project directory, run:

```bash
streamlit run app.py
```

Streamlit will provide a local URL, usually `http://localhost:8501`. Open it in your browser and upload a CSV that follows the required schema.

## Run the Notebook

Start Jupyter:

```bash
jupyter notebook
```

Open `ab_testing_analysis.ipynb` and run the cells from top to bottom. Make sure the dataset path in the notebook matches where you saved your CSV.

## Understanding the Statistics

- **Conversion rate:** conversions divided by users in a group.
- **Absolute lift:** treatment conversion rate minus control conversion rate, in percentage points.
- **Relative lift:** absolute lift divided by the control conversion rate, expressed as a percentage.
- **P-value:** evidence against the null hypothesis of equal conversion rates under the test assumptions. A small p-value does not measure the size or business importance of an effect.
- **Confidence interval:** a plausible range for the absolute difference in conversion rates.
- **SRM check:** checks whether observed group counts differ from the expected allocation. A flagged mismatch should be investigated before interpreting experiment results.
- **Statistical power and sample size:** help plan an experiment to detect a chosen minimum effect. Estimates depend on baseline conversion rate, significance level, allocation, and target power.

## Important Limitations

- Statistical significance does not automatically imply business value.
- A non-significant result does not prove the two variants are equivalent.
- SRM results depend on the expected allocation ratio and the data included in the check.
- Validate randomization, tracking, experiment duration, sample quality, and business guardrail metrics before making rollout decisions.
- The standard two-proportion test assumes independent observations and an appropriate experiment design.

## Future Improvements

- Add interactive SRM and power-calculator controls to the Streamlit app
- Export a cleaning report and experiment summary
- Add business guardrail metrics
- Add automated report downloads
- Add experiment visualizations and sensitivity analysis

## Author

**Abhinav Kumar**

- Portfolio: https://abhinav001-glitch.github.io/

## License

Choose a license before distributing the project. For a public portfolio repository, an MIT License is a common option, but only add it if you want to permit reuse under those terms.
