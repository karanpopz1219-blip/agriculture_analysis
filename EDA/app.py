import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import warnings

# Suppress warnings and set style
warnings.filterwarnings("ignore")
plt.style.use("ggplot")
sns.set_palette("viridis")

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="ICRISAT Agriculture Data Explorer",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌾 ICRISAT District-Level Agricultural Data Analysis")
st.markdown("### Explore crop production, yield, and area trends across Indian states")

# --- Sidebar: File Upload & Navigation ---
st.sidebar.header("📂 Upload Dataset")
uploaded_file = st.sidebar.file_uploader("Upload ICRISAT CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
else:
    st.warning("Please upload the **ICRISAT_District_Level_Data_Cleaned.csv** file to continue.")
    st.stop()

# --- Data Cleaning ---
prod_area_yield_cols = [col for col in df.columns if 'production' in col or 'area' in col or 'yield' in col]
df[prod_area_yield_cols] = df[prod_area_yield_cols].fillna(0)

# --- Sidebar Navigation ---
st.sidebar.header("🔍 Choose EDA Visualization")
eda_options = [
    "Top 7 Rice Producing States",
    "Top 5 Wheat Producing States",
    "Top 5 Oilseed Producing States",
    "Top 7 Sunflower Producing States",
    "Sugarcane, Rice & Wheat Time Series",
    "West Bengal Rice Production by District",
    "UP - Top 10 Wheat Production Years",
    "Sorghum Production by State",
    "Top 7 Groundnut Producing States",
    "Soybean Production & Yield Efficiency",
    "Top 10 Oilseed Producing States",
    "Area vs Production (Rice/Wheat/Maize)",
    "Rice vs Wheat Yield by State"
]
selected_analysis = st.sidebar.selectbox("Select Analysis:", eda_options)

# --- Helper: Plot Function Wrapper ---
def show_plot(fig):
    st.pyplot(fig)
    plt.close(fig)

# --- STATE COLUMN HANDLING ---
STATE_NAME = 'tate name'
YEAR = 'year'
DISTRICT_NAME = 'di_t name'

# --- Visualization Logic ---
if selected_analysis == "Top 7 Rice Producing States":
    rice_prod_state = df.groupby(STATE_NAME)['rice production _production_1000ton'].sum().nlargest(7)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=rice_prod_state.index, y=rice_prod_state.values, ax=ax, palette="Blues_d")
    ax.set_title("Top 7 Rice Producing States")
    ax.set_xlabel("State")
    ax.set_ylabel("Rice Production (1000 tons)")
    plt.xticks(rotation=45)
    show_plot(fig)

elif selected_analysis == "Top 5 Wheat Producing States":
    wheat_prod_state = df.groupby(STATE_NAME)['wheat production _production_1000ton'].sum().nlargest(5)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=wheat_prod_state.index, y=wheat_prod_state.values, ax=ax, palette="Reds_d")
    ax.set_title("Top 5 Wheat Producing States")
    plt.xticks(rotation=45)
    show_plot(fig)

    # Pie chart
    fig2, ax2 = plt.subplots(figsize=(6, 6))
    total = df['wheat production _production_1000ton'].sum()
    perc = (wheat_prod_state / total) * 100
    ax2.pie(perc, labels=perc.index, autopct="%1.1f%%", startangle=140)
    ax2.set_title("Wheat Production Share (%)")
    show_plot(fig2)

elif selected_analysis == "Top 5 Oilseed Producing States":
    oilseed_prod_state = df.groupby(STATE_NAME)['oil_eed_ production _production_1000ton'].sum().nlargest(5)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=oilseed_prod_state.index, y=oilseed_prod_state.values, ax=ax, palette="Greens_d")
    ax.set_title("Top 5 Oilseed Producing States")
    plt.xticks(rotation=45)
    show_plot(fig)

elif selected_analysis == "Top 7 Sunflower Producing States":
    sunflower_prod_state = df.groupby(STATE_NAME)['unflower production _production_1000ton'].sum().nlargest(7)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=sunflower_prod_state.index, y=sunflower_prod_state.values, ax=ax, palette="YlOrRd_d")
    ax.set_title("Top 7 Sunflower Producing States")
    plt.xticks(rotation=45)
    show_plot(fig)

elif selected_analysis == "Sugarcane, Rice & Wheat Time Series":
    ts = df.groupby(YEAR)[['ugarcane production _production_1000ton',
                           'rice production _production_1000ton',
                           'wheat production _production_1000ton']].sum().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=ts, x=YEAR, y='ugarcane production _production_1000ton', label='Sugarcane')
    sns.lineplot(data=ts, x=YEAR, y='rice production _production_1000ton', label='Rice')
    sns.lineplot(data=ts, x=YEAR, y='wheat production _production_1000ton', label='Wheat')
    ax.set_title("Production Trends Over Time")
    ax.legend()
    show_plot(fig)

elif selected_analysis == "West Bengal Rice Production by District":
    wb = df[df[STATE_NAME] == 'West Bengal']
    wb_rice = wb.groupby(DISTRICT_NAME)['rice production _production_1000ton'].sum().nlargest(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=wb_rice.index, y=wb_rice.values, ax=ax, palette="Oranges_d")
    ax.set_title("Rice Production by District (West Bengal)")
    plt.xticks(rotation=60)
    show_plot(fig)

elif selected_analysis == "UP - Top 10 Wheat Production Years":
    up = df[df[STATE_NAME] == 'Uttar Pradesh']
    up_year = up.groupby(YEAR)['wheat production _production_1000ton'].sum().nlargest(10)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=up_year.index.astype(str), y=up_year.values, ax=ax, palette="Purples_d")
    ax.set_title("Top 10 Wheat Production Years (Uttar Pradesh)")
    show_plot(fig)

elif selected_analysis == "Sorghum Production by State":
    sorghum = df.groupby(STATE_NAME)[['kharif _orghum production _production_1000ton',
                                      'rabi _orghum production _production_1000ton']].sum()
    fig, ax = plt.subplots(figsize=(12, 6))
    sorghum.plot(kind='bar', stacked=True, ax=ax, colormap='tab10')
    ax.set_title("Sorghum Production (Kharif & Rabi)")
    plt.xticks(rotation=45)
    show_plot(fig)

elif selected_analysis == "Top 7 Groundnut Producing States":
    groundnut = df.groupby(STATE_NAME)['groundnut production _production_1000ton'].sum().nlargest(7)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=groundnut.index, y=groundnut.values, ax=ax, palette="coolwarm")
    ax.set_title("Top 7 Groundnut Producing States")
    show_plot(fig)

elif selected_analysis == "Soybean Production & Yield Efficiency":
    soy = df.groupby(STATE_NAME).agg({
        'oyabean production _production_1000ton': 'sum',
        'oyabean yield _yield_kg_per_ha': 'mean'
    }).reset_index()
    top5 = soy.nlargest(5, 'oyabean production _production_1000ton')

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x=STATE_NAME, y='oyabean production _production_1000ton', data=top5, palette="plasma", ax=ax)
    ax.set_title("Top 5 Soybean Producing States")
    plt.xticks(rotation=45)
    show_plot(fig)

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sns.barplot(x=STATE_NAME, y='oyabean yield _yield_kg_per_ha', data=top5, palette="viridis", ax=ax2)
    ax2.set_title("Average Soybean Yield Efficiency")
    plt.xticks(rotation=45)
    show_plot(fig2)

elif selected_analysis == "Top 10 Oilseed Producing States":
    oil10 = df.groupby(STATE_NAME)['oil_eed_ production _production_1000ton'].sum().nlargest(10)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=oil10.index, y=oil10.values, ax=ax, palette="Oranges")
    ax.set_title("Top 10 Oilseed Producing States")
    plt.xticks(rotation=45)
    show_plot(fig)

elif selected_analysis == "Area vs Production (Rice/Wheat/Maize)":
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    sns.scatterplot(x='rice area _area_1000ha', y='rice production _production_1000ton', data=df, ax=axes[0], color='green')
    sns.scatterplot(x='wheat area _area_1000ha', y='wheat production _production_1000ton', data=df, ax=axes[1], color='red')
    sns.scatterplot(x='maize area _area_1000ha', y='maize production _production_1000ton', data=df, ax=axes[2], color='blue')
    axes[0].set_title('Rice')
    axes[1].set_title('Wheat')
    axes[2].set_title('Maize')
    show_plot(fig)

elif selected_analysis == "Rice vs Wheat Yield by State":
    yield_df = df.groupby(STATE_NAME)[['rice yield _yield_kg_per_ha', 'wheat yield _yield_kg_per_ha']].mean()
    fig, ax = plt.subplots(figsize=(14, 7))
    yield_df.plot(kind='bar', ax=ax, colormap='Accent')
    ax.set_title("Rice vs Wheat Yield (Average per State)")
    plt.xticks(rotation=45)
    show_plot(fig)

st.success("✅ Analysis Complete — Choose another visualization from the sidebar!")
