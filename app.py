from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

# Path to the Excel file
ACCIDENTS_FILE = "Dano.xls"
COMMENTS_FILE = "comments.csv"  # For persistent comment storage

# Ensure comment storage exists
if not os.path.exists(COMMENTS_FILE):
    pd.DataFrame(columns=["date", "cause", "comment"]).to_csv(COMMENTS_FILE, index=False)

# Load and process the Excel data
def load_data():
    df = pd.read_excel(ACCIDENTS_FILE, skiprows=4)
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    if "registro(data)" in df.columns:
        df["registro(data)"] = pd.to_datetime(df["registro(data)"], errors="coerce")
        df = df.set_index("registro(data)")

    colunas_pessoas_prejudicadas = [
        "dh_mortos", "dh_feridos", "dh_enfermos", "dh_desabrigados",
        "dh_desalojados", "dh_desaparecidos", "dh_outros_afetados"
    ]
    colunas_valores_destruicao = [col for col in df.columns if "valor" in col]

    for coluna in colunas_pessoas_prejudicadas + colunas_valores_destruicao:
        if coluna not in df.columns:
            df[coluna] = 0

    df["total_pessoas_prejudicadas"] = df[colunas_pessoas_prejudicadas].sum(axis=1)
    df["total_destruicao"] = df[colunas_valores_destruicao].sum(axis=1)

    return df

# Plot destruction chart
def plot_chart(df):
    chart_file = "static/chart.png"
    df["total_destruicao"].plot(kind="bar", figsize=(12, 6), color="orange", title="Total Destruction by Date")
    plt.xlabel("Date")
    plt.ylabel("Destruction Value (R$)")
    plt.tight_layout()
    plt.savefig(chart_file)
    plt.close()
    return chart_file

@app.route("/", methods=["GET", "POST"])
def index():
    df = load_data()
    chart_file = plot_chart(df)

    if request.method == "POST":
        # Handle 'Desabafe Aqui' form submission
        date = request.form["date"]
        cause = request.form["cause"]
        comment = request.form["comment"]

        # Append the comment to storage
        comments = pd.read_csv(COMMENTS_FILE)
        new_comment = pd.DataFrame([{"date": date, "cause": cause, "comment": comment}])
        comments = pd.concat([comments, new_comment], ignore_index=True)
        comments.to_csv(COMMENTS_FILE, index=False)
        return redirect(url_for("index"))

    # Prepare tragedy details
    top_tragedies = df.sort_values(
        by=["dh_mortos", "dh_feridos", "dh_desalojados", "total_destruicao"],
        ascending=[False, False, False, False]
    ).head(5).reset_index()

    comments = pd.read_csv(COMMENTS_FILE)
    return render_template("index.html", chart_file=chart_file, top_tragedies=top_tragedies.to_dict(orient="records"), comments=comments.to_dict(orient="records"))

if __name__ == "__main__":
    app.run(debug=True)
