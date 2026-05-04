import sqlite3
from datetime import datetime
import streamlit as st
import os

st.set_page_config(page_title="Service Vault", layout="wide")
DB_NAME = "service_vault.db"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# LOGIN
# =========================
AUTHORIZED_USERS = {
    "socio1": "SV!2026#Alpha",
    "socio2": "SV!2026#Beta",
    "socio3": "SV!2026#Gamma"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Service Vault Login")

    username = st.text_input("Usuário")
    password = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if username in AUTHORIZED_USERS and AUTHORIZED_USERS[username] == password:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Credenciais inválidas")

    st.stop()

# =========================
# DATABASE
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_type TEXT,
            company_name TEXT,
            created_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            description TEXT,
            file_path TEXT,
            created_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            category TEXT,
            amount REAL,
            note TEXT,
            created_at TEXT
        )
    ''')

    conn.commit()
    conn.close()


def execute(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    conn.close()


def fetch(query, params=()):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, params)
    data = c.fetchall()
    conn.close()
    return data

# =========================
# APP
# =========================
init_db()
st.title("Service Vault")

menu = st.sidebar.radio(
    "Navegação",
    [
        "Dashboard",
        "Cadastrar Empresa",
        "Registrar Evidência",
        "Registrar Gastos",
        "Pesquisar"
    ]
)

if st.sidebar.button("Sair"):
    st.session_state.logged_in = False
    st.rerun()

# DASHBOARD
if menu == "Dashboard":
    companies = fetch("SELECT * FROM companies")
    expenses = fetch("SELECT amount FROM expenses")

    total_expenses = sum(v[0] for v in expenses) if expenses else 0

    c1, c2 = st.columns(2)
    c1.metric("Empresas Registradas", len(companies))
    c2.metric("Gastos Totais", f"${total_expenses:,.2f}")

# REGISTER COMPANY
elif menu == "Cadastrar Empresa":
    with st.form("company_form"):
        service_type = st.selectbox(
            "Tipo de Serviço",
            ["SEO", "Landing Page", "Website", "Chatbot", "Leads"]
        )
        company_name = st.text_input("Empresa")

        if st.form_submit_button("Salvar"):
            execute(
                """
                INSERT INTO companies
                (service_type, company_name, created_at)
                VALUES (?, ?, ?)
                """,
                (service_type, company_name, str(datetime.now()))
            )
            st.success("Empresa registrada")

# EVIDENCE
elif menu == "Registrar Evidência":
    companies = fetch(
        "SELECT id, company_name, service_type FROM companies"
    )

    if companies:
        company_map = {
            f"{c[2]} - {c[1]}": c[0]
            for c in companies
        }

        with st.form("record_form"):
            selected = st.selectbox(
                "Selecionar Empresa",
                list(company_map.keys())
            )
            description = st.text_area("Descrição")
            uploaded_file = st.file_uploader(
                "Arquivo",
                type=["png", "jpg", "jpeg", "pdf", "mp4"]
            )

            if st.form_submit_button("Salvar"):
                file_path = ""

                if uploaded_file:
                    file_path = os.path.join(
                        UPLOAD_FOLDER,
                        uploaded_file.name
                    )
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                execute(
                    """
                    INSERT INTO records
                    (company_id, description, file_path, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        company_map[selected],
                        description,
                        file_path,
                        str(datetime.now())
                    )
                )
                st.success("Registro salvo")

# EXPENSES
elif menu == "Registrar Gastos":
    companies = fetch(
        "SELECT id, company_name, service_type FROM companies"
    )

    if companies:
        company_map = {
            f"{c[2]} - {c[1]}": c[0]
            for c in companies
        }

        with st.form("expense_form"):
            selected = st.selectbox(
                "Selecionar Empresa",
                list(company_map.keys())
            )
            category = st.text_input("Categoria")
            amount = st.number_input("Valor", min_value=0.0)
            note = st.text_input("Observação")

            if st.form_submit_button("Salvar"):
                execute(
                    """
                    INSERT INTO expenses
                    (company_id, category, amount, note, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        company_map[selected],
                        category,
                        amount,
                        note,
                        str(datetime.now())
                    )
                )
                st.success("Gasto registrado")

# SEARCH
elif menu == "Pesquisar":
    service_filter = st.selectbox(
        "Escolha o tipo de serviço",
        ["SEO", "Landing Page", "Website", "Chatbot", "Leads"]
    )

    companies = fetch(
        "SELECT id, company_name FROM companies WHERE service_type = ?",
        (service_filter,)
    )

    if companies:
        company_map = {
            c[1]: c[0]
            for c in companies
        }

        selected_company = st.selectbox(
            "Escolha a empresa",
            list(company_map.keys())
        )

        company_id = company_map[selected_company]

        st.subheader("Evidências")
        evidence = fetch(
            """
            SELECT description, file_path, created_at
            FROM records
            WHERE company_id = ?
            """,
            (company_id,)
        )
        st.dataframe(evidence)

        st.subheader("Gastos")
        expenses = fetch(
            """
            SELECT category, amount, note, created_at
            FROM expenses
            WHERE company_id = ?
            """,
            (company_id,)
        )
        st.dataframe(expenses)
