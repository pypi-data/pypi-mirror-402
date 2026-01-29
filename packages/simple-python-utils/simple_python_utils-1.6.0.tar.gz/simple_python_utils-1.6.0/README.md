<div align="center">

# 🐍 Simple Python Utils

*Uma biblioteca Python minimalista e elegante para funções utilitárias*

[![CI/CD Pipeline](https://github.com/fjmpereira20/simple-python-utils/actions/workflows/ci.yml/badge.svg)](https://github.com/fjmpereira20/simple-python-utils/actions/workflows/ci.yml)
[![PyPI Version](https://img.shields.io/pypi/v/simple-python-utils)](https://pypi.org/project/simple-python-utils/)
[![Python Version](https://img.shields.io/pypi/pyversions/simple-python-utils)](https://pypi.org/project/simple-python-utils/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Code Coverage](https://img.shields.io/codecov/c/github/fjmpereira20/simple-python-utils)](https://codecov.io/gh/fjmpereira20/simple-python-utils)
[![Code Quality](https://img.shields.io/codefactor/grade/github/fjmpereira20/simple-python-utils)](https://www.codefactor.io/repository/github/fjmpereira20/simple-python-utils)
[![PyPI Downloads](https://img.shields.io/pypi/dm/simple-python-utils)](https://pypi.org/project/simple-python-utils/)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

</div>

---

## ✨ Características

🎯 **Simples & Intuitivo** - API limpa e fácil de usar  
🔒 **Robusto & Confiável** - 100% cobertura de testes  
⚡ **Rápido & Eficiente** - Zero dependências externas  
🐍 **Python Puro** - Compatível com Python 3.9+

## 🎯 Objetivo

Este projeto demonstra boas práticas de desenvolvimento de pacotes Python, seguindo princípios de:
- **Simplicidade sobre complexidade**
- **Legibilidade sobre inteligência**
- **Clareza sobre abstração**

## 📦 Instalação

### 🚀 Instalação via PyPI (Recomendado)
```bash
# Instalação básica
pip install simple-python-utils

# Instalação com dependências de desenvolvimento
pip install simple-python-utils[dev]

# Instalação de versão específica
pip install simple-python-utils==1.5.0

# Upgrade para versão mais recente
pip install --upgrade simple-python-utils
```

### 🔧 Instalação via Git
```bash
# Instalação estável (branch main)
pip install git+https://github.com/fjmpereira20/simple-python-utils.git

# Instalação de desenvolvimento (branch develop)
pip install git+https://github.com/fjmpereira20/simple-python-utils.git@develop
```

### 🛠️ Instalação para Desenvolvimento
```bash
# Clonar repositório
git clone https://github.com/fjmpereira20/simple-python-utils.git
cd simple-python-utils

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalação em modo desenvolvimento
pip install -e ".[dev]"
```

### ✅ Verificação da Instalação
```python
# Verificar se a instalação funcionou
import simple_utils
print(f"Versão instalada: {simple_utils.__version__}")

# Testar funcionalidades básicas
from simple_utils import print_message, add_numbers
print_message("Instalação bem-sucedida!")
print(f"2 + 3 = {add_numbers(2, 3)}")
```

## 🚀 Uso Rápido

```python
from simple_utils import print_message, add_numbers, multiply_numbers, divide_numbers, square_numbers

# Imprimir mensagem
print_message("Olá, mundo!")
# Output: Olá, mundo!

# Somar números
resultado = add_numbers(3.5, 2.1)
print(f"Resultado: {resultado}")
# Output: Resultado: 5.6

# Multiplicar números
produto = multiply_numbers(4, 5)
print(f"Produto: {produto}")
# Output: Produto: 20

# Dividir números
divisao = divide_numbers(10, 2)
print(f"Divisão: {divisao}")
# Output: Divisão: 5.0

# Elevar ao quadrado
quadrado = square_numbers(6)
print(f"Quadrado: {quadrado}")
# Output: Quadrado: 36
```

## 📚 Funções Disponíveis

<div align="center">

| Função | Descrição | Exemplo | Resultado |
|--------|-----------|---------|-----------|
| `print_message(msg)` | Imprime mensagem com validação | `print_message("Hello!")` | `Hello!` |
| `add_numbers(a, b)` | Soma dois números | `add_numbers(2, 3)` | `5` |
| `multiply_numbers(a, b)` | Multiplica dois números | `multiply_numbers(4, 5)` | `20` |
| `divide_numbers(a, b)` | Divide dois números (proteção ÷0) | `divide_numbers(10, 2)` | `5.0` |
| `square_numbers(n)` | Eleva número ao quadrado | `square_numbers(6)` | `36` |

</div>

## 🧪 Executando os Testes

```bash
# Instalar dependências de teste
pip install -e ".[test]"

# Executar todos os testes
pytest

# Executar com cobertura
pytest --cov=simple_utils

# Executar testes específicos
pytest tests/test_core.py::TestPrintMessage::test_print_message_valid_string
```

## 🛠️ Desenvolvimento

### Configuração do Ambiente

```bash
# Clonar repositório
git clone https://github.com/fjmpereira20/simple-python-utils.git
cd simple-python-utils

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows

# Instalar em modo desenvolvimento
pip install -e ".[dev]"
```

### Ferramentas de Qualidade

```bash
# Formatação de código
black simple_utils/ tests/

# Organizar imports
isort simple_utils/ tests/

# Linting
flake8 simple_utils/ tests/

# Type checking
mypy simple_utils/

# Ou use o comando unificado:
make quality  # Linux/Mac
dev.bat quality  # Windows
```

### 🎨 Filosofia do Código

> "Simplicidade é a sofisticação máxima" - Leonardo da Vinci

Este projeto adota os seguintes princípios:

- ✅ **Claro > Inteligente**: Código autoexplicativo
- ✅ **Simples > Abstrato**: Evitar over-engineering
- ✅ **Legível > Compacto**: Priorizar compreensão
- ✅ **Funcional > Orientado a Objetos**: Usar funções puras
- ✅ **Documentado > Óbvio**: Docstrings e exemplos

## 🤝 Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'feat: add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- ✅ Mantenha o foco na simplicidade
- ✅ Adicione testes para novas funcionalidades
- ✅ Siga as convenções de código existentes
- ✅ Atualize a documentação conforme necessário
- ✅ Use [Conventional Commits](docs/CONVENTIONAL_COMMITS.md)

### 🤖 Changelog Automático
- **Local**: Use `make changelog` ou `dev.bat changelog` para preview
- **Automático**: Changelog gerado automaticamente em releases (`git tag v*`)
- **Baseado em**: [Conventional Commits](docs/CONVENTIONAL_COMMITS.md)

## 📚 Documentação

<div align="center">

### 📖 Guias Completos

| 📚 [Tutorial](docs/TUTORIAL.md) | 🔧 [API Reference](docs/API_REFERENCE.md) | ❓ [FAQ](docs/FAQ.md) |
|---|---|---|
| Guia passo a passo | Documentação técnica | Perguntas frequentes |

| 📝 [Commits](docs/CONVENTIONAL_COMMITS.md) | 📋 [Workflow](WORKFLOW.md) | 🤝 [Contribuindo](CONTRIBUTING.md) |
|---|---|---|
| Padrão de commits | Processo de dev | Como contribuir |

</div>

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

<div align="center">

**fjmpereira20**  
[![GitHub](https://img.shields.io/badge/GitHub-@fjmpereira20-blue?logo=github)](https://github.com/fjmpereira20)
[![Email](https://img.shields.io/badge/Email-fjmpereira20@users.noreply.github.com-red?logo=gmail)](mailto:fjmpereira20@users.noreply.github.com)

</div>

## 🌟 Agradecimentos

- Inspirado pelos princípios de design do Python (PEP 20 - The Zen of Python)
- Seguindo as melhores práticas da comunidade Python
- Focado em ser um exemplo de código limpo e bem documentado

---

<div align="center">

**Feito com ❤️ e Python**

</div>