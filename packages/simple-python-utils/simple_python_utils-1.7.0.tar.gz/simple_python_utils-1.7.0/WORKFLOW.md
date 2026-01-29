# Workflow de Desenvolvimento - Simple Python Utils 🔄

## 🌟 Estrutura de Branches

### 📋 Visão Geral
- **`main`** → 🏭 **Produção** (PyPI oficial)
- **`develop`** → 🧪 **Desenvolvimento** (TestPyPI)
- **`feature/*`** → ✨ **Features** (desenvolvimento local)
- **`bugfix/*`** → 🐛 **Correções** (desenvolvimento local)

## 🚀 Ambientes Automatizados

### 🧪 **Ambiente de Desenvolvimento**
- **Branch**: `develop`
- **Deploy automático**: TestPyPI quando há push
- **Testes**: Todos os OS e versões Python
- **URL**: https://test.pypi.org/project/simple-python-utils/
- **Instalação teste**: `pip install -i https://test.pypi.org/simple/ simple-python-utils`

### 🏭 **Ambiente de Produção** 
- **Branch**: `main`
- **Deploy automático**: PyPI oficial quando há tag `v*`
- **Release**: GitHub Release automático
- **URL**: https://pypi.org/project/simple-python-utils/
- **Instalação**: `pip install simple-python-utils`

## 📋 Fluxo de Trabalho

### 1️⃣ **Desenvolvimento de Features**

```bash
# Criar feature branch a partir do develop
git checkout develop
git pull origin develop
git checkout -b feature/nova-funcionalidade

# Desenvolver e testar
.\dev.bat quality

# Commit e push
git add .
git commit -m "feat: adicionar nova funcionalidade"
git push origin feature/nova-funcionalidade
```

### 2️⃣ **Pull Request para Desenvolvimento**
1. Abrir PR de `feature/nova-funcionalidade` → `develop`
2. CI/CD executa todos os testes
3. Code review (se necessário)
4. Merge para `develop`
5. **Deploy automático para TestPyPI** 🚀

### 3️⃣ **Teste no Ambiente de Desenvolvimento**
```bash
# Testar versão no TestPyPI
pip install -i https://test.pypi.org/simple/ simple-python-utils
python -c "from simple_utils import print_message; print_message('Teste OK!')"
```

### 4️⃣ **Promoção para Produção**
```bash
# PR do develop para main
git checkout main
git pull origin main
git checkout develop
git pull origin develop

# Criar PR develop → main
# Após aprovação e merge:
git checkout main
git pull origin main

# Criar tag de release
git tag v1.1.0
git push origin v1.1.0
```

### 5️⃣ **Release Automático** 🎉
- **Deploy automático**: PyPI oficial
- **GitHub Release**: Criado automaticamente
- **Changelog**: Atualizado automaticamente

## 🛡️ **Proteções de Branch**

### `main` (Produção)
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Restrict pushes that create files larger than 100MB
- ✅ Block force pushes

### `develop` (Desenvolvimento)  
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ⚠️ Allow force pushes (para desenvolvimento)

## 🔧 **Comandos Úteis**

### Desenvolvimento Local
```bash
# Setup inicial
git clone https://github.com/fjmpereira20/simple-python-utils.git
cd simple-python-utils
git checkout develop

# Instalar dependências
.\dev.bat install

# Workflow de desenvolvimento
.\dev.bat quality  # Testar tudo
```

### Verificar Status dos Ambientes
```bash
# Ver branches
git branch -a

# Ver tags
git tag -l

# Ver status CI/CD
# Ir para: https://github.com/fjmpereira20/simple-python-utils/actions
```

## 📦 **Versionamento Semântico**

- **Major** (v2.0.0): Breaking changes
- **Minor** (v1.1.0): Novas funcionalidades
- **Patch** (v1.0.1): Bug fixes

### Exemplos de Tags
```bash
git tag v1.0.1 -m "fix: correção de bug crítico"
git tag v1.1.0 -m "feat: nova funcionalidade importante" 
git tag v2.0.0 -m "feat!: mudanças que quebram compatibilidade"
```

## 🚨 **Emergências**

### Hotfix Direto em Produção
```bash
git checkout main
git checkout -b hotfix/critical-fix
# ... fazer correção ...
git commit -m "fix: correção crítica"
git push origin hotfix/critical-fix
# PR direto para main
# Após merge, fazer tag imediatamente
```

### Rollback Rápido
```bash
# Reverter para versão anterior
git checkout main
git revert HEAD
git push origin main
git tag v1.0.2 -m "fix: rollback para versão estável"
git push origin v1.0.2
```

## 📊 **Monitoramento**

- **CI/CD Status**: [GitHub Actions](https://github.com/fjmpereira20/simple-python-utils/actions)
- **Package Health**: [PyPI](https://pypi.org/project/simple-python-utils/)
- **Security**: [GitHub Security](https://github.com/fjmpereira20/simple-python-utils/security)
- **Dependencies**: Dependabot automático

---

## 🎯 **Resumo Rápido**

1. **Desenvolver**: Em `feature/*` branches
2. **Testar**: PR para `develop` → TestPyPI automático
3. **Produção**: PR `develop` → `main` + tag → PyPI automático
4. **Monitorar**: GitHub Actions + notificações

**Happy coding! 🐍✨**