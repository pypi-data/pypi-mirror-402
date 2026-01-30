# 📚 RuleField - Índice da Documentação

> Campo Django customizado para rule-engine com editor visual e validação dinâmica

## 🎯 Documentos Disponíveis

### Para Começar

1. **[INSTALL.md](./INSTALL.md)** - 📦 Instalação e Setup Inicial
   - O que foi criado
   - Como usar
   - Funcionalidades
   - Exemplo implementado
   - Testes
   - Próximos passos

2. **[QUICKSTART.md](./QUICKSTART.md)** - ⚡ Guia Rápido (5 minutos)
   - Instalação rápida em 4 passos
   - Sintaxe básica
   - Exemplos práticos
   - Troubleshooting
   - FAQ

### Documentação Completa

3. **[README.md](./README.md)** - 📖 Documentação Completa (450+ linhas)
   - Características detalhadas
   - Instalação
   - Uso básico e avançado
   - Sintaxe completa de regras
   - Usando no Django Admin
   - Validação programática
   - API de validação
   - Customização
   - Exemplo completo
   - Exemplos de regras por caso de uso
   - Troubleshooting
   - Referências

### Guias Especializados

4. **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** - 🔄 Guia de Migração
   - Migrar TextField existente
   - Aplicar em outro projeto
   - Customizar para necessidades específicas
   - Rollback/Reversão
   - Troubleshooting de migração
   - Checklist completo

### Código e Exemplos

5. **[examples.py](./EXAMPLES.md)** - 💻 Exemplos de Código (350+ linhas)
   - Exemplo 1: Uso básico
   - Exemplo 2: Com dados de exemplo
   - Exemplo 3: Validação de usuário
   - Exemplo 4: Regra de desconto
   - Exemplo 5: Múltiplas regras
   - Lista de regras comuns

7. **[VISUAL_DEMO.py](./VISUAL_DEMO.md)** - 🎨 Demonstração Visual
   - Definição no modelo
   - Aparência no admin
   - Fluxo de uso
   - Exemplos de validação
   - Cores e temas
   - Atalhos de teclado
   - Responsividade
   - Animações
   - Acessibilidade
   - Compatibilidade

### Scripts Utilitários

8. **[setup.sh](./setup.sh)** - 🔧 Script de Setup Automatizado
   - Verifica dependências
   - Cria migrations
   - Aplica migrations
   - Coleta arquivos estáticos
   - Executa testes

### Arquivos de Código

9. **[rule_field.py](./rule_field.py)** - Campo Django customizado
10. **[rule_widget.py](./rule_widget.py)** - Widget para o admin
11. **[../templates/widgets/rule_widget.html](../templates/widgets/rule_widget.html)** - Template HTML
12. **[../static/rule_widget/rule_widget.js](../static/rule_widget/rule_widget.js)** - JavaScript
13. **[../static/rule_widget/rule_widget.css](../static/rule_widget/rule_widget.css)** - CSS
14. **[../api/views.py](../api/views.py)** - API endpoint
15. **[../api/urls.py](../api/urls.py)** - URLs da API

---

## 🚀 Por Onde Começar?

### Sou Novo no RuleField
1. Leia: **[INSTALL.md](./INSTALL.md)** (3 min)
2. Leia: **[QUICKSTART.md](./QUICKSTART.md)** (5 min)
3. Execute: `bash setup.sh`
4. Teste no admin!

### Quero Usar no Meu Projeto
1. Leia: **[README.md](./README.md)** seção "Uso Básico"
2. Copie os arquivos necessários
3. Siga: **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** seção 2

### Preciso Customizar
1. Leia: **[README.md](./README.md)** seção "Customização"
2. Veja: **[examples.py](./examples.py)** para inspiração
3. Consulte: **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** seção 3

### Quero Ver Como Funciona
1. Abra: **[VISUAL_DEMO.py](./VISUAL_DEMO.py)**
2. Veja: **[examples.py](./examples.py)**
3. Execute: `python manage.py shell < test_rule_field.py`

### Tenho um Problema
1. Consulte: **[QUICKSTART.md](./QUICKSTART.md)** seção "Troubleshooting"
2. Veja: **[README.md](./README.md)** seção "Troubleshooting"
3. Confira: **[MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)** seção "Troubleshooting"

---

## 📊 Resumo por Tipo de Documento

### 📘 Documentação Geral
- INSTALL.md - Instalação inicial
- README.md - Documentação completa
- QUICKSTART.md - Início rápido

### 🔧 Guias Técnicos
- MIGRATION_GUIDE.md - Migração e customização

### 💻 Código e Exemplos
- examples.py - 5 exemplos completos
- test_rule_field.py - Suite de testes
- VISUAL_DEMO.py - Demonstração visual

### 🛠️ Arquivos de Implementação
- rule_field.py - Campo Django
- rule_widget.py - Widget
- rule_widget.html - Template
- rule_widget.js - JavaScript
- rule_widget.css - CSS
- views.py - API
- urls.py - URLs

### ⚙️ Scripts
- setup.sh - Setup automatizado

---

## 📈 Estatísticas

- **Total de Documentos:** 15 arquivos
- **Linhas de Documentação:** ~1.500+
- **Linhas de Código:** ~700+
- **Exemplos Funcionais:** 5+
- **Suites de Teste:** 5
- **Casos de Uso Cobertos:** 10+

---

## 🔗 Links Externos

- [rule-engine no PyPI](https://pypi.org/project/rule-engine/)
- [Documentação rule-engine](https://zerosteiner.github.io/rule-engine/)
- [Django Custom Model Fields](https://docs.djangoproject.com/en/stable/howto/custom-model-fields/)
- [CodeMirror](https://codemirror.net/)

---

## 📝 Convenções de Nomenclatura

- `RuleField` - Classe do campo Django
- `RuleWidget` - Classe do widget
- `rule_field.py` - Arquivo do campo
- `rule_widget.*` - Arquivos do widget
- `/api/validate-rule/` - Endpoint da API

---

## 🎓 Níveis de Experiência

| Nível | Documento Recomendado |
|-------|----------------------|
| Iniciante | INSTALL.md → QUICKSTART.md |
| Intermediário | README.md → examples.py |
| Avançado | MIGRATION_GUIDE.md → Código fonte |
| Contribuidor | Todos os arquivos |

---

## 🗺️ Mapa do Conhecimento

```
┌─────────────────────────────────────────────────────────┐
│                  COMEÇAR AQUI                           │
│                  ↓                                      │
│            [INSTALL.md]                                 │
│                  ↓                                      │
│            [QUICKSTART.md]                              │
│                  ↓                                      │
│         Precisa de mais detalhes?                       │
│                  ↓                                      │
│    ┌────────────┴─────────────┐                        │
│    ↓                           ↓                        │
│ [README.md]              [examples.py]                  │
│    ↓                           ↓                        │
│ Customizar?                 Ver testes?                 │
│    ↓                           ↓                        │
│ [MIGRATION_GUIDE.md]    [test_rule_field.py]           │
│    ↓                           ↓                        │
│ Ver visual?                Tudo OK!                     │
│    ↓                                                    │
│ [VISUAL_DEMO.py]                                        │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Aprendizado

- [ ] Li INSTALL.md e entendi o que foi criado
- [ ] Segui QUICKSTART.md e instalei com sucesso
- [ ] Li README.md e entendi a sintaxe de regras
- [ ] Vi examples.py e entendi casos de uso
- [ ] Executei test_rule_field.py com sucesso
- [ ] Testei no Django Admin
- [ ] Criei minha primeira regra
- [ ] Validei uma regra dinamicamente
- [ ] Li MIGRATION_GUIDE.md para customizar
- [ ] Implementei em meu projeto

---

## 💡 Dicas Finais

1. **Começe Simples** - Use exemplos básicos primeiro
2. **Teste Sempre** - Valide suas regras no admin antes de usar
3. **Leia os Exemplos** - O arquivo examples.py tem muitos casos práticos
4. **Use o Atalho** - Ctrl+Enter para validar é mais rápido
5. **Customize** - O campo é flexível, adapte para sua necessidade

---

**Versão:** 1.0.0  
**Última Atualização:** Janeiro 2026  
**Criado para:** Projeto AVA - IFRN  
**Licença:** Mesmo do projeto principal

---

📧 **Precisa de ajuda?** Consulte a documentação relevante acima!
