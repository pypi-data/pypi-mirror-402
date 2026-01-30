# RuleField - Campo Django para Rule Engine

✨ **Campo Django customizado com editor visual e validação dinâmica**

## 📦 O que foi criado?

### Estrutura de Arquivos

```
src/base/
├── fields/
│   ├── __init__.py           # Exporta RuleField
│   ├── rule_field.py         # Campo Django customizado
│   ├── rule_widget.py        # Widget para o admin
│   ├── README.md             # Documentação completa
│   ├── QUICKSTART.md         # Guia rápido
│   ├── examples.py           # Exemplos de código
│   └── test_rule_field.py    # Script de testes
├── templates/
│   └── widgets/
│       └── rule_widget.html  # Template do widget
├── static/
│   └── rule_widget/
│       ├── rule_widget.js    # JavaScript do widget
│       └── rule_widget.css   # Estilos
└── api/
    ├── __init__.py
    ├── views.py              # Endpoint de validação
    └── urls.py               # URLs da API
```

## 🚀 Como Usar

### 1. Uso Básico

```python
from django_rule_engine.fields import RuleField

class MeuModelo(models.Model):
    regra = RuleField(
        verbose_name="Regra de Validação",
        example_data={"idade": 25, "status": "ativo"}
    )
```

### 2. Criar Migrations

```bash
cd src/
python manage.py makemigrations
python manage.py migrate
```

### 3. Coletar Arquivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 4. Testar no Admin

1. Acesse o Django Admin
2. Edite um objeto com RuleField
3. Veja o editor com syntax highlighting
4. Digite uma regra (ex: `idade >= 18 and status == "ativo"`)
5. Clique em **Validar** ou pressione **Ctrl+Enter**
6. Veja o resultado da validação

## ✨ Funcionalidades

- ✅ Editor de código com syntax highlighting (CodeMirror)
- ✅ Campo JSON de exemplo editável pelo usuário
- ✅ Validação dinâmica em tempo real
- ✅ Feedback visual (sucesso/erro)
- ✅ Atalhos de teclado (Ctrl+Enter para validar)
- ✅ API REST para validação
- ✅ Validação no backend
- ✅ Documentação completa
- ✅ Exemplos práticos

## 📝 Exemplos de Regras

```python
# Idade mínima
"idade >= 18"

# Múltiplas condições
"idade >= 18 and status == 'ativo'"

# Email institucional
'"@ifrn.edu.br" in email'

# Regras complexas
"(preco > 100 or quantidade >= 5) and tipo_cliente == 'premium'"

# Com funções
"len(nome) > 3 and idade >= 18"
```

## 🔧 Exemplo Implementado

O campo já está implementado no modelo `Cohort` em [coorte/models.py](../../../coorte/models.py):

```python
class Cohort(models.Model):
    name = CharField("cohort name", max_length=256, unique=True)
    rule = RuleField(
        "validation rule",
        blank=True,
        null=True,
        example_data={
            "login": "usuario123",
            "user": {"email": "usuario@example.com"},
            "name": "João da Silva",
            "status": "Ativo"
        },
        default="login == 'usuario123' and user.email != 'usuario123@example.com'",
    )

    class Meta:
        verbose_name = _("cohort")
        verbose_name_plural = _("cohorts")
        ordering = ["name"]

    def __str__(self):
        return self.name

```

## 🧪 Testes

Execute os testes:

```bash
cd src/
python manage.py shell
```

Dentro do shell:

```python
from django_rule_engine.fields.test_rule_field import test_all
test_all()
```

Ou diretamente:

```bash
python manage.py shell < base/fields/test_rule_field.py
```

## 📚 Documentação

- **[README.md](./README.md)** - Documentação completa e detalhada
- **[QUICKSTART.md](./QUICKSTART.md)** - Guia rápido de início
- **[examples.py](./examples.py)** - Exemplos de código prontos para usar

## 🌐 API

O endpoint de validação está disponível em:

```
POST /api/validate-rule/

Body:
{
    "rule": "idade >= 18 and status == 'ativo'",
    "data": {"idade": 25, "status": "ativo"}
}

Response:
{
    "valid": true,
    "result": true,
    "matches": true
}
```

## 🎯 Próximos Passos

1. ✅ **Implementar no seu modelo** - Adicione `RuleField` onde precisar
2. ✅ **Criar migrations** - `python manage.py makemigrations`
3. ✅ **Aplicar migrations** - `python manage.py migrate`
4. ✅ **Testar no admin** - Acesse e edite um objeto
5. ✅ **Usar programaticamente** - Veja exemplos em `examples.py`

## 💡 Dicas

- Use `blank=True, null=True` se o campo for opcional
- Defina `example_data` relevante para seu caso de uso
- Teste suas regras no admin antes de usar em produção
- Consulte a [documentação do rule-engine](https://zerosteiner.github.io/rule-engine/)

## ❓ Suporte

- Leia [README.md](./README.md) para documentação completa
- Veja [examples.py](./examples.py) para casos de uso
- Consulte [QUICKSTART.md](./QUICKSTART.md) para início rápido

## 📄 Licença

Segue a licença do projeto principal.

---

**Criado com ❤️ para o projeto AVA do IFRN**
