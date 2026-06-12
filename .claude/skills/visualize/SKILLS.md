---
name: visualize
description: Visualizes data using various libraries and tools.
--- 

## Usage

### Step-1: Pick the python environment
Before you start, make sure to pick the python environment in which you want to run the code. You can run/install dependencies using my '.venv' environment which is located at "C:\ClaudeCode\.venv"

### Step-2: Use Pandas to Build KPIs
- You need to read the parquet files stored in the latest folder at ".claude/skills/migrate/data". 
- After reading the data, you need to use pandas to build the following KPIs:
    - Total Sales
    - Total Returns
    - Net Sales
    - Average Sales per Store
    - Average Sales per Product
    - Average Sales per Customer

### Step 3: Use Matplotlib/Seaborn to Build Visualization
- After building the KPIs, you need to use Matplotlib/Seaborn to build the following visualizations:
    - Sales Trend Over Time
    - Sales by Store
    - Sales by Product
    - Sales by Customer
    - Returns Trend Over Time
    - Returns by Store
    - Returns by Product
    - Returns by Customer
- You need to save the visualization as PNG files in the folder with the same name as source folder (datetime) ".claude/skills/visualize/visualizations/" using plt.savefig() function.