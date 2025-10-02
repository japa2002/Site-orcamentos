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

# Carrega backups existentes
def load_backups():
    backups = {}
    for filename in os.listdir(BACKUP_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(BACKUP_DIR, filename), 'r') as f:
                backups[filename[:-5]] = json.load(f)
    return backups

# Salva backup em arquivo
def save_backup(backup_key, backup_data):
    with open(os.path.join(BACKUP_DIR, f"{backup_key}.json"), 'w') as f:
        json.dump(backup_data, f)

# Inicializa session_state
if 'itens' not in st.session_state:
    st.session_state.itens = []
if 'imported' not in st.session_state:
    st.session_state.imported = False
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

# Sidebar pra dados do cliente e empresa
st.sidebar.header("Dados da Empresa (Edite uma vez)")
empresa_nome = st.sidebar.text_input("Nome da Marcenaria", value="AW Marcenaria Móveis Sob Medida")
empresa_endereco = st.sidebar.text_input("Endereço da Empresa", value="Rua Brusque, 880, Bairro Glória - Blumenau - SC")

st.sidebar.header("Dados do Cliente")
cliente_nome = st.sidebar.text_input("Nome do Cliente", value=st.session_state.cliente_nome, key="cliente_input")
cliente_telefone = st.sidebar.text_input("Telefone do Cliente", value=st.session_state.cliente_telefone, key="telefone_input")
cliente_endereco = st.sidebar.text_area("Endereço do Cliente", value=st.session_state.cliente_endereco, key="endereco_input")
projetos_nome = st.sidebar.text_input("Nome do Projeto (opcional)", value=st.session_state.projetos_nome, key="projetos_input")

# Seção de Importar Backup
st.subheader("Importar Backup")
uploaded_file = st.file_uploader("Escolha um arquivo JSON de backup", type="json")
if uploaded_file is not None and not st.session_state.imported:
    try:
        backup_data = json.load(uploaded_file)
        st.session_state.itens = backup_data.get('itens', []).copy()
        if 'cliente_nome' in backup_data:
            st.session_state.cliente_nome = backup_data['cliente_nome']
            cliente_nome = st.session_state.cliente_nome
        if 'cliente_telefone' in backup_data:
            st.session_state.cliente_telefone = backup_data['cliente_telefone']
            cliente_telefone = st.session_state.cliente_telefone
        if 'cliente_endereco' in backup_data:
            st.session_state.cliente_endereco = backup_data['cliente_endereco']
            cliente_endereco = st.session_state.cliente_endereco
        if 'projetos_nome' in backup_data:
            st.session_state.projetos_nome = backup_data['projetos_nome']
            projetos_nome = st.session_state.projetos_nome
        if 'orcamento_valido_por' in backup_data:
            st.session_state.orcamento_valido_por = backup_data['orcamento_valido_por']
        st.success("Backup importado com sucesso!")
        st.session_state.imported = True
    except Exception as e:
        st.error(f"Erro ao importar: {e}")

# Botão pra restaurar orçamento
st.subheader("Restaurar Orçamento")
if cliente_nome and st.session_state.backups:
    cliente_backups = {k: v for k, v in st.session_state.backups.items() if v['cliente_nome'] == cliente_nome}
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
            cliente_nome = st.session_state.cliente_nome
            cliente_telefone = st.session_state.cliente_telefone
            cliente_endereco = st.session_state.cliente_endereco
            prazo = backup_data.get('prazo', '')
            pagamento = backup_data.get('pagamento', '')
            orcamento_valido_por = backup_data.get('orcamento_valido_por', '')
            observacao = backup_data.get('observacao', '')
            st.rerun()
    else:
        st.write(f"Nenhum backup encontrado para {cliente_nome}.")
elif cliente_nome:
    st.write(f"Nenhum backup encontrado para {cliente_nome}.")

# Interface principal
st.header("Adicionar/Editar Itens Sob Medida")

# Se está editando, preenche com dados do item
editing_item = None
if st.session_state.editing_index is not None:
    editing_item = st.session_state.itens[st.session_state.editing_index]

# Colunas pra input
col1, col2, col3 = st.columns(3)
with col1:
    item_nome = st.text_input("Nome do Item", value=editing_item['Item'] if editing_item else "")
with col2:
    qtd = st.number_input("Quantidade", min_value=1, value=editing_item['Qtd'] if editing_item else 1)
with col3:
    preco_unit = st.number_input("Preço Unitário (R$)", min_value=0.0, value=editing_item['Preço Unit'] if editing_item else 0.0)

# Campos de texto com layout responsivo
especificacoes = st.text_area("Especificações", value=editing_item['Especificações'] if editing_item else "", height=100)
material = st.text_input("Material", value=editing_item['Material'] if editing_item else "")

# Botão para adicionar ou atualizar item
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
            
            st.session_state.imported = False
            st.rerun()
        else:
            st.error("Preencha nome e preço!")

with col_btn2:
    if editing_item:
        if st.button("❌ Cancelar", use_container_width=True):
            st.session_state.editing_index = None
            st.rerun()

# Exibe tabela de itens com opção de editar/remover
if st.session_state.itens:
    df = pd.DataFrame(st.session_state.itens)
    st.subheader("Resumo dos Itens")
    
    for index, row in df.iterrows():
        with st.expander(f"{row['Item']} - Qtd: {row['Qtd']}", expanded=(index == st.session_state.editing_index)):
            st.write(f"**Material:** {row['Material']}")
            st.write(f"**Especificações:** {row['Especificações']}")
            st.write(f"**Subtotal:** R$ {row['Subtotal']:.2f}")
            
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
            st.subheader(f"Total Geral: R$ {total:.2f}")
            st.subheader(f"Valor Final: R$ {valor_final:.2f}")
        else:
            st.subheader(f"Valor Final: R$ {valor_final:.2f}")

    # Extras
    st.subheader("Condições")
    col_c, col_d, col_e = st.columns(3)
    with col_c:
        prazo = st.text_input("Prazo de entrega")
    with col_d:
        pagamento = st.text_input("Forma de pagamento")
    with col_e:
        orcamento_valido_por = st.text_input("Orçamento válido por")

    # Campos de texto com layout responsivo para mobile
    observacao = st.text_area("Observações", height=100, help="Ex: Entrega inclui instalação")
    itens_inclusos = st.text_area("Itens Inclusos", height=100, help="Ex: Manutenção básica")
    itens_nao_inclusos = st.text_area("Itens Não Inclusos", height=100, help="Ex: Transporte")

    # Botão pra salvar backup do orçamento
    if st.button("💾 Salvar Orçamento como Backup", use_container_width=True):
        if cliente_nome and st.session_state.itens:
            backup_key = f"{cliente_nome}_{datetime.now().strftime('%Y%m%d_%H%M')}"
            backup_data = {
                'itens': st.session_state.itens.copy(),
                'cliente_nome': cliente_nome,
                'cliente_telefone': cliente_telefone,
                'cliente_endereco': cliente_endereco,
                'projetos_nome': projetos_nome,
                'prazo': prazo,
                'pagamento': pagamento,
                'orcamento_valido_por': orcamento_valido_por,
                'observacao': observacao,
                'itens_inclusos': itens_inclusos,
                'itens_nao_inclusos': itens_nao_inclusos,
                'total': total,
                'desconto': desconto,
                'valor_final': valor_final
            }
            save_backup(backup_key, backup_data)
            st.session_state.backups = load_backups()
            st.success(f"✅ Orçamento salvo para {cliente_nome}!")

    # Botão pra gerar PDF
    if st.button("📄 Gerar e Baixar PDF", use_container_width=True):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=36)
        styles = getSampleStyleSheet()

        # Conteúdo do PDF
        elements = []

        # Cabeçalho com logo
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

        # Itens Inclusos
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

        # Itens Não Inclusos
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

        # Gera o PDF
        doc.build(elements)
        buffer.seek(0)

        # Nome do arquivo com nome do cliente
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