# Site-orcamentos
# AW Marcenaria - Gerador de Orçamentos Sob Medida

Bem-vindo ao **Gerador de Orçamentos Sob Medida**, uma aplicação web desenvolvida para a AW Marcenaria Móveis Sob Medida. Este projeto permite criar orçamentos personalizados para móveis sob medida, gerar PDFs profissionais e gerenciar backups de orçamentos. A aplicação é construída com [Streamlit](https://streamlit.io/) e hospedada gratuitamente no Streamlit Community Cloud.

## Funcionalidades
- **Criação de Orçamentos**: Adicione itens sob medida com detalhes como nome, quantidade, preço unitário, especificações e material.
- **Cálculo Automático**: Calcule subtotais e aplique descontos para obter o valor final.
- **Geração de PDF**: Exporte orçamentos em formato PDF com layout profissional, incluindo o logotipo da empresa, dados do cliente, itens, condições e observações.
- **Backups**: Salve e restaure orçamentos em formato JSON para facilitar o gerenciamento.
- **Campos Personalizáveis**: Inclua informações da empresa (nome e endereço), cliente, projetos, prazo de entrega, forma de pagamento e validade do orçamento.
- **Interface Responsiva**: Funciona em desktops, tablets e celulares.

## Estrutura do Projeto
- `app.py`: Script principal da aplicação Streamlit.
- `requirements.txt`: Lista de dependências Python necessárias.
- `Logo.jpg`: Arquivo de logotipo da AW Marcenaria (necessário para o PDF).
- `backups/`: Diretório para armazenar backups temporários em formato JSON.

## Como Rodar Localmente
### Pré-requisitos
- Python 3.7 ou superior
- Git (opcional, para clonar o repositório)

### Passos
1. **Clone o repositório**:
   ```bash
   git clone https://github.com/<seu-usuario>/<nome-do-repositorio>.git
   cd <nome-do-repositorio>
