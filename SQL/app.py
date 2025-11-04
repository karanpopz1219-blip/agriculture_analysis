import streamlit as st
import pandas as pd
import sqlite3
import warnings
import re
import os

# Suppress warnings
warnings.filterwarnings('ignore')

# --- 1. Database Setup and Data Loading (Encapsulated for Streamlit) ---

@st.cache_resource
def initialize_database(csv_file: str):
    """
    Connects to a file-based SQLite database, loads the CSV,
    cleans the data, renames columns, and writes it to the database.
    This function is cached by Streamlit to run only once.
    """
    DB_NAME = 'temp_icrisat.db'  # Persistent database file
    TABLE_NAME = 'ICRISAT_District_Level_Data_Cleaned'

    try:
        # Connect to the SQLite database (thread-safe)
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        cursor = conn.cursor()

        # Check if the CSV file exists
        if not os.path.exists(csv_file):
            st.error(f"Error: The file '{csv_file}' was not found. Please ensure it is in the same directory.")
            return None, None  # Return None if setup fails

        # Load the CSV into a Pandas DataFrame
        df = pd.read_csv(csv_file)

        # Normalize column names: strip whitespace
        df.columns = [c.strip() for c in df.columns]

        # --- Helper functions for column normalization and finding ---
        def normalize(colname: str) -> str:
            return re.sub(r'[^a-z0-9]', '', colname.lower())

        normalized_map = {col: normalize(col) for col in df.columns}

        def find_col_with_tokens(tokens):
            norm_tokens = [t.replace('_', '').lower() for t in tokens]
            for orig, norm in normalized_map.items():
                if all(tok in norm for tok in norm_tokens):
                    return orig
            return None
        # --- End of Helper functions ---

        rename_map = {}
        # Year
        c = find_col_with_tokens(['year'])
        if c:
            rename_map[c] = 'Year'
        # State and District names
        c = find_col_with_tokens(['state', 'name']) or find_col_with_tokens(['tate', 'name'])
        if c:
            rename_map[c] = 'StateName'
        c = find_col_with_tokens(['district', 'name']) or find_col_with_tokens(['di', 'name'])
        if c:
            rename_map[c] = 'DistrictName'

        # Common production / area / yield columns used in queries (best-effort)
        prod_mappings = [
            (['rice', 'production'], 'RiceProd'),
            (['wheat', 'production'], 'WheatProd'),
            (['oilseed', 'production'], 'OilseedProd'),
            (['cotton', 'production'], 'CottonProd'),
            (['groundnut', 'production'], 'GroundnutProd'),
            (['maize', 'yield'], 'MaizeYield'),
            (['rice', 'yield'], 'RiceYield'),
            (['wheat', 'yield'], 'WheatYield'),
            (['oilseed', 'area'], 'OilseedArea'),
            (['oil', 'eed', 'area'], 'OilseedArea'),
            (['oil', 'eed', 'production'], 'OilseedProd'),
            (['oil', 'eed', 'yield'], 'OilseedYield')
        ]

        for toks, target in prod_mappings:
            c = find_col_with_tokens(toks)
            if c and c not in rename_map:
                rename_map[c] = target

        if rename_map:
            df = df.rename(columns=rename_map)

        # Fill NaNs with 0 before importing to ensure proper number handling in SQL
        prod_area_yield_cols = [col for col in df.columns if ('Prod' in col or 'Area' in col or 'Yield' in col)]
        if prod_area_yield_cols:
            df[prod_area_yield_cols] = df[prod_area_yield_cols].fillna(0)

        # Write the cleaned DataFrame to the SQLite table
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)

        # Get MAX Year for use in queries
        max_year_result = cursor.execute(f"SELECT MAX(Year) FROM {TABLE_NAME}").fetchone()
        MAX_YEAR = max_year_result[0]

        st.success(f"✅ Database setup complete. Data loaded for years {df['Year'].min()} to {MAX_YEAR}.")
        return conn, MAX_YEAR

    except Exception as e:
        st.error(f"An error occurred during database setup: {e}")
        return None, None


# --- Main Streamlit App Logic ---

def main():
    st.set_page_config(layout="wide", page_title="ICRISAT Data Analytics")

    st.title("🌾 Agricultural Data Analytics Dashboard")
    st.markdown("Use this dashboard to run pre-defined SQL queries on the **ICRISAT District-Level Data**.")

    CSV_FILE = 'ICRISAT_District_Level_Data_Cleaned.csv'
    TABLE_NAME = 'ICRISAT_District_Level_Data_Cleaned'

    # Initialize the database and get the connection and MAX_YEAR
    conn, MAX_YEAR = initialize_database(CSV_FILE)

    if conn is None or MAX_YEAR is None:
        st.stop()  # Stop the app if initialization failed

    # --- 2. SQL Queries Definition (Dynamically generated with MAX_YEAR) ---

    sql_queries = {
        "Q1: Year-wise Trend of Rice Production Across States (Top 3)": f"""
            WITH TopStates AS (
                SELECT StateName FROM {TABLE_NAME}
                GROUP BY StateName ORDER BY SUM(RiceProd) DESC LIMIT 3
            )
            SELECT T1.Year, T1.StateName, SUM(T1.RiceProd) AS TotalRiceProduction_1000Tons
            FROM {TABLE_NAME} T1 JOIN TopStates TS ON T1.StateName = TS.StateName
            GROUP BY T1.Year, T1.StateName
            ORDER BY T1.StateName, T1.Year;
        """,

        "Q2: Top 5 Districts by Wheat Yield Increase Over the Last 5 Years": f"""
            WITH YieldsByYear AS (
                SELECT DistrictName,
                    AVG(CASE WHEN Year = {MAX_YEAR} THEN WheatYield END) AS Yield_EndYear,
                    AVG(CASE WHEN Year = {MAX_YEAR - 4} THEN WheatYield END) AS Yield_StartYear
                FROM {TABLE_NAME}
                WHERE Year IN ({MAX_YEAR}, {MAX_YEAR - 4})
                GROUP BY DistrictName
            )
            SELECT DistrictName, Yield_StartYear, Yield_EndYear,
                (Yield_EndYear - Yield_StartYear) AS Yield_Increase
            FROM YieldsByYear
            WHERE Yield_StartYear IS NOT NULL AND Yield_EndYear IS NOT NULL
            ORDER BY Yield_Increase DESC
            LIMIT 5;
        """,

        "Q3: States with the Highest Growth in Oilseed Production (5-Year Growth Rate)": f"""
            WITH StateProduction AS (
                SELECT StateName,
                    SUM(CASE WHEN Year BETWEEN 1990 AND 1994 THEN OilseedProd ELSE 0 END) AS Prod_A,
                    SUM(CASE WHEN Year BETWEEN {MAX_YEAR - 4} AND {MAX_YEAR} THEN OilseedProd ELSE 0 END) AS Prod_B
                FROM {TABLE_NAME}
                GROUP BY StateName
            )
            SELECT StateName, Prod_A, Prod_B,
                ((CAST(Prod_B AS REAL) / NULLIF(Prod_A, 0)) - 1) * 100 AS Growth_Rate_Percent
            FROM StateProduction
            WHERE Prod_A > 0
            ORDER BY Growth_Rate_Percent DESC
            LIMIT 5;
        """,

        "Q4: District-wise Correlation Between Area and Production for Major Crops (Rice, Wheat, Maize)": f"""
            SELECT DistrictName,
                'N/A (Use external tool for correlation)' AS Correlation_Result
            FROM {TABLE_NAME}
            GROUP BY DistrictName
            HAVING COUNT(Year) > 5
            LIMIT 5;
        """,

        "Q5: Yearly Production Growth of Cotton in Top 5 Cotton Producing States": f"""
            WITH TopStates AS (
                SELECT StateName FROM {TABLE_NAME}
                GROUP BY StateName ORDER BY SUM(CottonProd) DESC LIMIT 5
            ),
            StateYearProd AS (
                SELECT T1.Year, T1.StateName, SUM(T1.CottonProd) AS Current_Prod
                FROM {TABLE_NAME} T1 JOIN TopStates TS ON T1.StateName = TS.StateName
                GROUP BY T1.Year, T1.StateName
            ),
            GrowthRate AS (
                SELECT StateName,
                    (Current_Prod - LAG(Current_Prod, 1) OVER (PARTITION BY StateName ORDER BY Year)) AS Prod_Change,
                    LAG(Current_Prod, 1) OVER (PARTITION BY StateName ORDER BY Year) AS Prev_Prod
                FROM StateYearProd
            )
            SELECT StateName,
                AVG((CAST(Prod_Change AS REAL) / NULLIF(Prev_Prod, 0))) * 100 AS Avg_Annual_Growth_Rate_Percent
            FROM GrowthRate
            WHERE Prev_Prod > 0
            GROUP BY StateName
            ORDER BY Avg_Annual_Growth_Rate_Percent DESC;
        """,

        "Q6: Districts with the Highest Groundnut Production in Latest Year": f"""
            SELECT DistrictName, SUM(GroundnutProd) AS TotalGroundnutProduction_1000Tons
            FROM {TABLE_NAME}
            WHERE Year = {MAX_YEAR}
            GROUP BY DistrictName
            ORDER BY TotalGroundnutProduction_1000Tons DESC
            LIMIT 5;
        """,

        "Q7: Annual Average Maize Yield Across All States": f"""
            SELECT Year, AVG(MaizeYield) AS Annual_Average_Maize_Yield_kg_per_ha
            FROM {TABLE_NAME}
            GROUP BY Year
            ORDER BY Year DESC;
        """,

        "Q8: Total Area Cultivated for Oilseeds in Each State": f"""
            SELECT StateName, SUM(OilseedArea) AS Total_Oilseed_Area_1000ha
            FROM {TABLE_NAME}
            GROUP BY StateName
            ORDER BY Total_Oilseed_Area_1000ha DESC
            LIMIT 10;
        """,

        "Q9: Districts with the Highest Rice Yield": f"""
            SELECT DistrictName, AVG(RiceYield) AS Average_Rice_Yield_kg_per_ha
            FROM {TABLE_NAME}
            GROUP BY DistrictName
            ORDER BY Average_Rice_Yield_kg_per_ha DESC
            LIMIT 5;
        """,

        "Q10: Compare the Production of Wheat and Rice for the Top 5 States Over 10 Years": f"""
            WITH TopStates AS (
                SELECT StateName FROM {TABLE_NAME}
                GROUP BY StateName ORDER BY SUM(RiceProd + WheatProd) DESC LIMIT 5
            )
            SELECT T1.Year, T1.StateName,
                SUM(T1.RiceProd) AS TotalRiceProduction_1000Tons,
                SUM(T1.WheatProd) AS TotalWheatProduction_1000Tons
            FROM {TABLE_NAME} T1 JOIN TopStates TS ON T1.StateName = TS.StateName
            WHERE T1.Year >= {MAX_YEAR - 9}
            GROUP BY T1.Year, T1.StateName
            ORDER BY T1.StateName, T1.Year;
        """,
    }

    # --- 3. Streamlit UI for Query Selection and Execution ---

    st.sidebar.header("Select a Query")

    # Dropdown to select a query
    selected_query_title = st.sidebar.selectbox(
        "Choose an analysis question:",
        list(sql_queries.keys())
    )

    # Get the SQL for the selected query
    selected_sql = sql_queries[selected_query_title]

    st.header(f"📊 {selected_query_title}")

    # Display the SQL code
    with st.expander("View SQL Query"):
        st.code(selected_sql, language='sql')

    # Execute the query
    try:
        # Execute the query and fetch the results into a DataFrame
        result_df = pd.read_sql_query(selected_sql, conn)

        st.subheader("Results")
        if not result_df.empty:
            # Display the DataFrame
            st.dataframe(result_df)

            # Optional: Display a chart for relevant queries
            if "Q1:" in selected_query_title or "Q7:" in selected_query_title or "Q10:" in selected_query_title:
                st.subheader("Visualization")

                if "Q1:" in selected_query_title:
                    st.line_chart(result_df, x='Year', y='TotalRiceProduction_1000Tons', color='StateName')
                elif "Q7:" in selected_query_title:
                    st.line_chart(result_df.set_index('Year'))
                elif "Q10:" in selected_query_title:
                    chart_df = result_df.melt(
                        id_vars=['Year', 'StateName'],
                        var_name='Crop',
                        value_name='Production (1000 Tons)'
                    )
                    st.line_chart(chart_df, x='Year', y='Production (1000 Tons)', color='Crop')

        else:
            st.info("The query returned no results.")

    except Exception as e:
        st.error(f"**Query Execution Error:** {e}")
        st.code(selected_sql)

if __name__ == '__main__':
    main()
