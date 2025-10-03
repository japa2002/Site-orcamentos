import streamlit as st
import pandas as pd
import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, Image
from io import BytesIO
from datetime import datetime
import re

# Usar pdfplumber em vez de PyPDF2 para extração mais confiável
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

# Config da página
st.set_page_config(page_title="Orçamentos Sob Medida", layout="wide")
st.title("🛠️ Gerador de Orçamentos Sob Medida")

# CSS customizado para os botões
st.markdown("""
<style>
.stButton>button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
}
.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.6);
}
.stDownloadButton>button {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%) !important;
    color: white !important;
    font-weight: bold !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px 0 rgba(17, 153, 142, 0.4) !important;
}
.stDownloadButton>button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px 0 rgba(17, 153, 142, 0.6) !important;
}
</style>
""", unsafe_allow_html=True)

# Diretório para backups
BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

def load_backups():
    backups = {}
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BACKUP_DIR, filename), 'r', encoding='utf-8') as f:
                try:
                    backups[filename[:-5]] = json.load(f)
                except Exception as e:
                    print("Erro ao ler backup JSON:", filename, e)
    return backups

def save_backup(backup_key, backup_data):
    with open(os.path.join(BACKUP_DIR, f"{backup_key}.json"), 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

def extrair_dados_pdf(pdf_file):
    """Extrai informações do PDF do orçamento usando pdfplumber."""
    if pdfplumber is None:
        st.error("pdfplumber não está instalado. Instale com: pip install pdfplumber")
        return None
    try:
        dados = {
            'cliente_nome': '',
            'cliente_telefone': '',
            'cliente_endereco': '',
            'projetos_nome': '',
            'prazo': '',
            'pagamento': '',
            'orcamento_valido_por': '',
            'observacao': '',
            'itens_inclusos': '',
            'itens_nao_inclusos': '',
            'itens': []
        }

        with pdfplumber.open(pdf_file) as pdf:
            texto_completo = ""
            tabelas = []
            for page in pdf.pages:
                # Extrai texto bruto
                texto = page.extract_text()
                if texto:
                    texto_completo += texto + "\n"
                # Extrai tabelas da página
                tabelas_pagina = page.extract_tables()
                tabelas.extend(tabelas_pagina)

            # DEBUG: gravar o texto extraído para análise
            try:
                with open("debug_texto_extraido.txt", "w", encoding="utf-8") as f:
                    f.write(texto_completo)
            except Exception as e:
                print("Não foi possível gravar debug_texto_extraido.txt:", e)

            # Para facilitar comparações
            texto_lower = texto_completo.lower()

            # Extração de dados gerais
            match = re.search(r'cliente[:\s]+(.+?)(?:\n|telefone)', texto_lower, re.IGNORECASE)
            if match:
                dados['cliente_nome'] = match.group(1).strip().title()

            match = re.search(r'telefone[:\s]+(.+?)(?:\n|endereço)', texto_lower, re.IGNORECASE)
            if match:
                dados['cliente_telefone'] = match.group(1).strip()

            match = re.search(r'endereço[:\s]+(.+?)(?:\n{2,}|item)', texto_lower, re.IGNORECASE | re.DOTALL)
            if match:
                dados['cliente_endereco'] = match.group(1).strip().title()

            match = re.search(r'prazo de entrega[:\s]+(.+?)(?:\n|forma)', texto_lower, re.IGNORECASE)
            if match:
                dados['prazo'] = match.group(1).strip().title()

            match = re.search(r'forma de pagamento[:\s]+(.+?)(?:\n|orçamento)', texto_lower, re.IGNORECASE)
            if match:
                dados['pagamento'] = match.group(1).strip().title()

            match = re.search(r'orçamento válido por[:\s]+(.+?)(?:\n|observações)', texto_lower, re.IGNORECASE)
            if match:
                dados['orcamento_valido_por'] = match.group(1).strip().title()

            match = re.search(r'observações[:\s]+(.+?)(?:\n{2,}|itens inclusos)', texto_lower, re.IGNORECASE | re.DOTALL)
            if match:
                dados['observacao'] = match.group(1).strip().capitalize()

            match = re.search(r'itens inclusos[:\s]+(.+?)(?:\n{2,}|itens não inclusos)', texto_lower, re.IGNORECASE | re.DOTALL)
            if match:
                dados['itens_inclusos'] = match.group(1).strip().capitalize()

            match = re.search(r'itens não inclusos[:\s]+(.+?)(?:\n{2,}|móveis conforme|$)', texto_lower, re.IGNORECASE | re.DOTALL)
            if match:
                dados['itens_nao_inclusos'] = match.group(1).strip().capitalize()

            match = re.search(r'projetos[:\s]+(.+)$', texto_lower, re.IGNORECASE)
            if match:
                dados['projetos_nome'] = match.group(1).strip().title()

            # Extração de itens da tabela usando pdfplumber
            for tabela in tabelas:
                if not tabela or len(tabela) < 2:
                    continue

                cabecalho = [h.lower() if h else '' for h in tabela[0]]
                idx_item = idx_qtd = idx_espec = idx_material = idx_subtotal = -1
                for i, col in enumerate(cabecalho):
                    if 'item' in col:
                        idx_item = i
                    elif 'qtd' in col or 'quantidade' in col:
                        idx_qtd = i
                    elif 'especificações' in col or 'especificacao' in col:
                        idx_espec = i
                    elif 'material' in col:
                        idx_material = i
                    elif 'subtotal' in col or 'valor' in col:
                        idx_subtotal = i

                for linha in tabela[1:]:
                    if any(keyword in (''.join(linha).lower()) for keyword in ['total', 'condições', 'observações']):
                        continue

                    item_nome = ''
                    qtd = 1
                    especificacoes = ''
                    material = ''
                    subtotal = 0.0

                    if idx_item != -1 and len(linha) > idx_item and linha[idx_item]:
                        item_nome = linha[idx_item].strip()
                    if idx_qtd != -1 and len(linha) > idx_qtd and linha[idx_qtd]:
                        try:
                            qtd = int(re.search(r'\d+', linha[idx_qtd]).group())
                        except:
                            qtd = 1
                    if idx_espec != -1 and len(linha) > idx_espec and linha[idx_espec]:
                        especificacoes = linha[idx_espec].strip()
                    if idx_material != -1 and len(linha) > idx_material and linha[idx_material]:
                        material = linha[idx_material].strip()
                    if idx_subtotal != -1 and len(linha) > idx_subtotal and linha[idx_subtotal]:
                        valor_str = re.search(r'[\d\.,]+', linha[idx_subtotal])
                        if valor_str:
                            subtotal_str = valor_str.group().replace('.', '').replace(',', '.')
                            try:
                                subtotal = float(subtotal_str)
                            except:
                                subtotal = 0.0

                    preco_unit = subtotal / qtd if qtd > 0 and subtotal > 0 else subtotal

                    if item_nome and subtotal > 0:
                        dados['itens'].append({
                            'Item': item_nome,
                            'Qtd': qtd,
                            'Especificações': especificacoes,
                            'Material': material,
                            'Preço Unit': round(preco_unit, 2),
                            'Subtotal': round(subtotal, 2)
                        })

            if not dados['itens']:
                linhas = texto_completo.splitlines()
                capturando = False
                for linha in linhas:
                    low = linha.lower()
                    if ('item' in low and 'qtd' in low and 'subtotal' in low) or ('item' in low and 'subtotal' in low):
                        capturando = True
                        continue
                    if capturando:
                        if 'total geral' in low or 'valor final' in low or 'condições' in low:
                            break
                        if re.search(r'r\$\s?\d', linha, re.IGNORECASE):
                            subtimos = re.findall(r'R\$\s*([\d\.,]+)', linha)
                            if not subtimos:
                                continue
                            subtotal_str = subtimos[-1].replace('.', '').replace(',', '.')
                            try:
                                subtotal = float(subtotal_str)
                            except:
                                continue
                            partes = linha.split()
                            qtd = 1
                            nome_parts = []
                            for p in partes:
                                if re.fullmatch(r'\d+', p):
                                    qtd = int(p)
                                    continue
                                if 'r$' in p.lower():
                                    break
                                nome_parts.append(p)
                            nome_item = ' '.join(nome_parts).strip()
                            if nome_item:
                                preco_unit = subtotal / qtd if qtd > 0 else subtotal
                                dados['itens'].append({
                                    'Item': nome_item,
                                    'Qtd': qtd,
                                    'Especificações': '',
                                    'Material': '',
                                    'Preço Unit': round(preco_unit, 2),
                                    'Subtotal': round(subtotal, 2)
                                })

        return dados
    except Exception as e:
        st.error(f"Erro ao processar PDF: {str(e)}")
        return None

# Inicializa session_state
if 'itens' not in st.session_state:
    st.session_state.itens = []
if 'cliente_nome' not in st.session_state:
    st.session_state.cliente_nome = ""
if 'cliente_telefone' not in st.session_state:
    st.session_state.cliente_telefone = ""
if 'cliente_endereco' not in st.session_state:
    st.session_state.cliente_endereco = ""
if 'projetos_nome' not in st.session_state:
    st.session_state.projetos_nome = ""
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
st.session_state.backups = load_backups()

# Sidebar para dados da empresa / cliente
st.sidebar.header("Dados da Empresa (Edite uma vez)")
empresa_nome = st.sidebar.text_input("Nome da Marcenaria", value="AW Marcenaria Móveis Sob Medida")
empresa_endereco = st.sidebar.text_input("Endereço da Empresa", value="Rua Brusque, 880, Bairro Glória - Blumenau - SC")

st.sidebar.header("Dados do Cliente")
cliente_nome = st.sidebar.text_input("Nome do Cliente", value=st.session_state.cliente_nome, key="cliente_input")
cliente_telefone = st.sidebar.text_input("Telefone do Cliente", value=st.session_state.cliente_telefone, key="telefone_input")
cliente_endereco = st.sidebar.text_area("Endereço do Cliente", value=st.session_state.cliente_endereco, key="endereco_input")
projetos_nome = st.sidebar.text_input("Nome do Projeto (opcional)", value=st.session_state.projetos_nome, key="projetos_input")

# Importar PDF
st.subheader("📄 Importar Orçamento de PDF")
st.info("💡 Carregue um PDF de orçamento anterior para editar. O sistema vai extrair automaticamente os dados!")
if pdfplumber is None:
    st.warning("⚠️ Para usar esta função, é necessário instalar pdfplumber. Execute: pip install pdfplumber")
uploaded_pdf = st.file_uploader("Escolha um arquivo PDF de orçamento", type="pdf", key="pdf_uploader")
if uploaded_pdf is not None:
    with st.spinner("Extraindo dados do PDF..."):
        dados_extraidos = extrair_dados_pdf(uploaded_pdf)
    if dados_extraidos:
        st.success("✅ PDF processado com sucesso!")
        with st.expander("📋 Visualizar dados extraídos", expanded=True):
            col_prev1, col_prev2 = st.columns(2)
            with col_prev1:
                st.write(f"**Cliente:** {dados_extraidos['cliente_nome']}")
                st.write(f"**Telefone:** {dados_extraidos['cliente_telefone']}")
                st.write(f"**Itens encontrados:** {len(dados_extraidos['itens'])}")
            with col_prev2:
                st.write(f"**Prazo:** {dados_extraidos['prazo']}")
                st.write(f"**Pagamento:** {dados_extraidos['pagamento']}")
                st.write(f"**Validade:** {dados_extraidos['orcamento_valido_por']}")
        if st.button("✅ Confirmar e Carregar Dados do PDF", use_container_width=True):
            st.session_state.cliente_nome = dados_extraidos['cliente_nome']
            st.session_state.cliente_telefone = dados_extraidos['cliente_telefone']
            st.session_state.cliente_endereco = dados_extraidos['cliente_endereco']
            st.session_state.projetos_nome = dados_extraidos['projetos_nome']
            st.session_state.itens = dados_extraidos['itens'].copy()
            st.session_state.prazo_temp = dados_extraidos['prazo']
            st.session_state.pagamento_temp = dados_extraidos['pagamento']
            st.session_state.orcamento_valido_por_temp = dados_extraidos['orcamento_valido_por']
            st.session_state.observacao_temp = dados_extraidos['observacao']
            st.session_state.itens_inclusos_temp = dados_extraidos['itens_inclusos']
            st.session_state.itens_nao_inclusos_temp = dados_extraidos['itens_nao_inclusos']
            st.success("🎉 Dados carregados! Agora você pode editar o que precisar.")
            st.rerun()

# Restaurar orçamento via backup
st.subheader("Restaurar Orçamento")
if cliente_nome and st.session_state.backups:
    cliente_backups = {k: v for k, v in st.session_state.backups.items() if v.get('cliente_nome') == cliente_nome}
    if cliente_backups:
        backup_options = list(cliente_backups.keys())
        selected_backup = st.selectbox("Selecione o backup:", backup_options)
        if st.button("Restaurar Orçamento Selecionado", key="restore"):
            backup_data = cliente_backups[selected_backup]
            st.session_state.itens = backup_data['itens'].copy()
            st.session_state.cliente_nome = backup_data['cliente_nome']
            st.session_state.cliente_telefone = backup_data['cliente_telefone']
            st.session_state.cliente_endereco = backup_data['cliente_endereco']
            st.session_state.projetos_nome = backup_data.get('projetos_nome', '')
            st.session_state.orcamento_valido_por = backup_data.get('orcamento_valido_por', '')
            st.rerun()
    else:
        st.write(f"Nenhum backup encontrado para {cliente_nome}.")
elif cliente_nome:
    st.write(f"Nenhum backup encontrado para {cliente_nome}.")

# Interface principal: adicionar/editar itens
st.header("Adicionar/Editar Itens Sob Medida")
editing_item = None
if st.session_state.editing_index is not None:
    editing_item = st.session_state.itens[st.session_state.editing_index]

col1, col2, col3 = st.columns(3)
with col1:
    item_nome = st.text_input("Nome do Item", value=editing_item['Item'] if editing_item else "")
with col2:
    qtd = st.number_input("Quantidade", min_value=1, value=editing_item['Qtd'] if editing_item else 1)
with col3:
    preco_unit = st.number_input("Preço Unitário (R$)", min_value=0.0, value=editing_item['Preço Unit'] if editing_item else 0.0)

especificacoes = st.text_area("Especificações", value=editing_item['Especificações'] if editing_item else "", height=100)
material = st.text_input("Material", value=editing_item['Material'] if editing_item else "")

col_btn1, col_btn2 = st.columns([3, 1])
with col_btn1:
    button_label = "✏️ Atualizar Item" if editing_item else "➕ Adicionar Item"
    if st.button(button_label, use_container_width=True):
        if item_nome and preco_unit > 0:
            novo_item = {
                'Item': item_nome,
                'Qtd': qtd,
                'Especificações': especificacoes,
                'Material': material,
                'Preço Unit': preco_unit,
                'Subtotal': qtd * preco_unit
            }
            if editing_item:
                st.session_state.itens[st.session_state.editing_index] = novo_item
                st.session_state.editing_index = None
                st.success("Item atualizado!")
            else:
                st.session_state.itens.append(novo_item)
                st.success("Item adicionado!")
            st.rerun()
        else:
            st.error("Preencha nome e preço!")
with col_btn2:
    if editing_item:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.editing_index = None
            st.rerun()

if st.session_state.itens:
    df = pd.DataFrame(st.session_state.itens)
    st.subheader("Resumo dos Itens")
    for index, row in df.iterrows():
        with st.expander(f"{row['Item']} - Qtd: {row['Qtd']}", expanded=(index == st.session_state.editing_index)):
            st.write(f"**Material:** {row['Material']}")
            st.write(f"**Especificações:** {row['Especificações']}")
            st.write(f"**Subtotal:** R$ {row['Subtotal']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✏️ Editar", key=f"editar_{index}", use_container_width=True):
                    st.session_state.editing_index = index
                    st.rerun()
            with col_b:
                if st.button("❌ Remover", key=f"remover_{index}", use_container_width=True):
                    st.session_state.itens.pop(index)
                    if st.session_state.editing_index == index:
                        st.session_state.editing_index = None
                    st.rerun()

    total = df['Subtotal'].sum()
    col_a, col_b = st.columns(2)
    with col_a:
        desconto = st.number_input("Desconto %", min_value=0.0, max_value=100.0, value=0.0)
    with col_b:
        valor_final = total * (1 - desconto / 100)
    if desconto > 0:
        st.subheader(f"Total Geral: R$ {total:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
        st.subheader(f"Valor Final: R$ {valor_final:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))
    else:
        st.subheader(f"Valor Final: R$ {valor_final:,.2f}".replace('.', '#').replace(',', '.').replace('#', ','))

st.subheader("Condições")
col_c, col_d, col_e = st.columns(3)
with col_c:
    prazo = st.text_input("Prazo de entrega", value=st.session_state.get('prazo_temp', ''))
with col_d:
    pagamento = st.text_input("Forma de pagamento", value=st.session_state.get('pagamento_temp', ''))
with col_e:
    orcamento_valido_por = st.text_input("Orçamento válido por", value=st.session_state.get('orcamento_valido_por_temp', ''))

observacao = st.text_area("Observações", height=100, help="Ex: Entrega inclui instalação", value=st.session_state.get('observacao_temp', ''))
itens_inclusos = st.text_area("Itens Inclusos", height=100, help="Ex: Manutenção básica", value=st.session_state.get('itens_inclusos_temp', ''))
itens_nao_inclusos = st.text_area("Itens Não Inclusos", height=100, help="Ex: Transporte", value=st.session_state.get('itens_nao_inclusos_temp', ''))

if st.button("📄 Gerar e Baixar PDF", use_container_width=True):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=36)
    styles = getSampleStyleSheet()
    elements = []

    # Cabeçalho
    logo_path = os.path.join(os.path.dirname(__file__), "Logo.jpg")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(BACKUP_DIR, "Logo.jpg")
    header_data = [[Paragraph(f"<b>{empresa_nome}</b>", styles['Heading1']), ""]]
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=1*inch, height=1*inch)
        header_data[0][1] = logo
    header_table = Table(header_data, colWidths=[5.5*inch, 0.5*inch])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(Paragraph(f"{empresa_endereco}", styles['Normal']))
    elements.append(Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Dados do cliente
    elements.append(Paragraph("<b>Orçamento</b>", styles['Heading2']))
    elements.append(Paragraph(f"Cliente: {cliente_nome or 'Não especificado'}", styles['Normal']))
    elements.append(Paragraph(f"Telefone: {cliente_telefone or 'Não especificado'}", styles['Normal']))
    elements.append(Paragraph(f"Endereço: {cliente_endereco or 'Não especificado'}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Tabela de itens
    if st.session_state.itens:
        df = pd.DataFrame(st.session_state.itens)
        table_data = [["Item", "Qtd", "Especificações", "Material", "Subtotal"]]
        for _, row in df.iterrows():
            espec_lines = row['Especificações'].split('\n')
            full_spec = "<br/>".join(espec_lines)
            table_data.append([
                Paragraph(row['Item'], styles['Normal']),
                str(row['Qtd']),
                Paragraph(full_spec, styles['Normal']),
                row['Material'][:15],
                f"R$ {row['Subtotal']:,.2f}".replace('.', '#').replace(',', '.').replace('#', ',')
            ])
        table = Table(table_data, colWidths=[1.5*inch, 0.5*inch, 3*inch, 1.5*inch, 1*inch])
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#D3D3D3'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#000000'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
        table.setStyle(style)
        elements.append(table)

    # Totais
    elements.append(Spacer(1, 12))
    total = df['Subtotal'].sum() if st.session_state.itens else 0
    valor_final = total * (1 - desconto / 100)
    if desconto > 0:
        elements.append(Paragraph(f"<b>Total Geral: R$ {total:,.2f}</b>".replace('.', '#').replace(',', '.').replace('#', ','), styles['Heading2']))
        elements.append(Paragraph(f"<b>Valor Final: R$ {valor_final:,.2f}</b>".replace('.', '#').replace(',', '.').replace('#', ','), styles['Heading2']))
    else:
        elements.append(Paragraph(f"<b>Valor Final: R$ {valor_final:,.2f}</b>".replace('.', '#').replace(',', '.').replace('#', ','), styles['Heading2']))

    # Condições
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("<b>Condições:</b>", styles['Heading2']))
    elements.append(Paragraph(f"Prazo de entrega: {prazo}", styles['Normal']))
    elements.append(Paragraph(f"Forma de pagamento: {pagamento}", styles['Normal']))
    elements.append(Paragraph(f"Orçamento válido por: {orcamento_valido_por}", styles['Normal']))

    # Observações
    if observacao:
        elements.append(Spacer(1, 12))
        observacao_table = Table([[Paragraph(f"<b>Observações:</b><br/>{observacao}", styles['Normal'])]], colWidths=[6*inch])
        observacao_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), '#F0F0F0'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])
        observacao_table.setStyle(observacao_style)
        elements.append(observacao_table)
        elements.append(Spacer(1, 12))

    # Itens inclusos
    if itens_inclusos:
        elements.append(Spacer(1, 12))
        inclusos_table = Table([[Paragraph(f"<b>Itens Inclusos:</b><br/>{itens_inclusos}", styles['Normal'])]], colWidths=[6*inch])
        inclusos_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), '#F0F0F0'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])
        inclusos_table.setStyle(inclusos_style)
        elements.append(inclusos_table)
        elements.append(Spacer(1, 12))

    # Itens não inclusos
    if itens_nao_inclusos:
        elements.append(Spacer(1, 12))
        nao_inclusos_table = Table([[Paragraph(f"<b>Itens Não Inclusos:</b><br/>{itens_nao_inclusos}", styles['Normal'])]], colWidths=[6*inch])
        nao_inclusos_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), '#F0F0F0'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])
        nao_inclusos_table.setStyle(nao_inclusos_style)
        elements.append(nao_inclusos_table)
        elements.append(Spacer(1, 12))

    # Texto final
    elements.append(Paragraph("Móveis conforme projetos com garantia de dois anos.", styles['Normal']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<u>Att. Genesio e Sidnei</u>", styles['Normal']))
    if projetos_nome:
        elements.append(Paragraph(f"Projetos: {projetos_nome}", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    nome_arquivo = f"orcamento_{cliente_nome.replace(' ', '_')}_{datetime.now().strftime('%d-%m-%Y')}.pdf" if cliente_nome else f"orcamento_{datetime.now().strftime('%d-%m-%Y')}.pdf"
    st.download_button(
        label="📄 Baixar Orçamento em PDF",
        data=buffer,
        file_name=nome_arquivo,
        mime="application/pdf",
        use_container_width=True
    )

st.sidebar.markdown("---")
st.sidebar.info("💡 **Dica**: Agora você pode editar itens após adicionar! Clique em 'Editar' em qualquer item.")