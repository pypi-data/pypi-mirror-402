# Simple Python Utils 🐍

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Uma biblioteca Python minimalista com funções utilitárias básicas, focada em simplicidade e clareza.

## 🎯 Objetivo

Este projeto demonstra boas práticas de desenvolvimento de pacotes Python, seguindo princípios de:
- **Simplicidade sobre complexidade**
- **Legibilidade sobre inteligência**
- **Clareza sobre abstração**

## 📦 Instalação

### Instalação via Git
```bash
git clone https://github.com/fjmpereira20/simple-python-utils.git
cd simple-python-utils
pip install -e .
```

### Instalação para Desenvolvimento
```bash
git clone https://github.com/fjmpereira20/simple-python-utils.git
cd simple-python-utils
pip install -e ".[dev]"
```

## 🚀 Uso Rápido

```python
from simple_utils import print_message, add_numbers

# Imprimir mensagem
print_message("Olá, mundo!")
# Output: Olá, mundo!

# Somar números
resultado = add_numbers(3.5, 2.1)
print(f"Resultado: {resultado}")
# Output: Resultado: 5.6

# Somar inteiros
soma = add_numbers(10, 25)
print(f"Soma: {soma}")
# Output: Soma: 35
```

## 📚 Documentação das Funções

### `print_message(message: str) -> None`

Imprime uma mensagem no stdout com validação de tipo.

**Parâmetros:**
- `message` (str): A mensagem a ser impressa

**Raises:**
- `TypeError`: Se a mensagem não for uma string

**Exemplos:**
```python
print_message("Hello, World!")
print_message("Mensagem com acentos: ção, ã, é")
print_message("")  # String vazia é válida
```

### `add_numbers(a: Union[int, float], b: Union[int, float]) -> Union[int, float]`

Soma dois números com validação de tipos.

**Parâmetros:**
- `a` (int | float): Primeiro número
- `b` (int | float): Segundo número

**Retorna:**
- `int`: Se ambos os números forem inteiros
- `float`: Se pelo menos um número for float

**Raises:**
- `TypeError`: Se algum parâmetro não for numérico

**Exemplos:**
```python
add_numbers(2, 3)        # Retorna: 5 (int)
add_numbers(2.5, 1.5)    # Retorna: 4.0 (float)
add_numbers(10, 3.14)    # Retorna: 13.14 (float)
add_numbers(-5, 3)       # Retorna: -2 (int)
```

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
```

### Estrutura do Projeto
```
simple-python-utils/
├── simple_utils/          # Código fonte do pacote
│   ├── __init__.py       # Exportações e metadados
│   └── core.py          # Funções principais
├── tests/                # Testes automatizados
│   ├── __init__.py
│   └── test_core.py
├── README.md            # Esta documentação
├── setup.py            # Configuração do pacote
├── requirements.txt    # Dependências de desenvolvimento
├── LICENSE            # Licença MIT
└── prompt_inicial.md  # Especificações do projeto
```

## 🎨 Filosofia do Código

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
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

### Diretrizes de Contribuição

- Mantenha o foco na simplicidade
- Adicione testes para novas funcionalidades
- Siga as convenções de código existentes
- Atualize a documentação conforme necessário
- Não adicione dependências externas sem discussão

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 Autor

**fjmpereira20**
- GitHub: [@fjmpereira20](https://github.com/fjmpereira20)
- Email: your.email@example.com

## 🌟 Agradecimentos

- Inspirado pelos princípios de design do Python (PEP 20 - The Zen of Python)
- Seguindo as melhores práticas da comunidade Python
- Focado em ser um exemplo de código limpo e bem documentado

---

**Feito com ❤️ e Python**
