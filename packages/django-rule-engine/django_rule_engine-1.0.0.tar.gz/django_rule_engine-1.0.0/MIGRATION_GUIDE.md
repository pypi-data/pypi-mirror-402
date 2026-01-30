# 🔄 Guia de Migração do RuleField

Este guia explica como migrar o RuleField para outros projetos Django ou adaptar campos existentes.

## 📋 Índice

1. [Migrar TextField Existente](#migrar-textfield-existente)
2. [Aplicar em Outro Projeto](#aplicar-em-outro-projeto)
3. [Customizar para Necessidades Específicas](#customizar-para-necessidades-específicas)
4. [Rollback/Reversão](#rollbackreversão)

---

## 1. Migrar TextField Existente

Se você já tem um campo `TextField` com regras e quer converter para `RuleField`:

### Passo 1: Backup do Banco

```bash
python manage.py dumpdata seu_app.SeuModelo > backup_modelo.json
```

### Passo 2: Atualizar o Modelo

**Antes:**
```python
class Cohort(models.Model):
    name = CharField("cohort name", max_length=256, unique=True)
    rule = TextField("validation rule"))
```

**Depois:**
```python
from django_rule_engine.fields import RuleField

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
```

### Passo 3: Criar Migration

```bash
python manage.py makemigrations
```

### Passo 4: Verificar Migration Gerada

A migration deve mostrar algo como:

```python
operations = [
    migrations.AlterField(
        model_name='cohort',
        name='rule',
        field=django_rule_engine.fields.RuleField(
            blank=True,
            example_data={'login': 'usuario123', ...},
            null=True,
            verbose_name='regra de validação'
        ),
    ),
]
```

### Passo 5: Aplicar Migration

```bash
python manage.py migrate
```

**Nota:** Como `RuleField` herda de `TextField`, os dados existentes serão preservados!

### Passo 6: Validar Regras Existentes

Execute este script para validar todas as regras existentes:

```python
# validate_existing_rules.py
import rule_engine
from seu_app.models import SeuModelo

def validar_regras():
    objetos = SeuModelo.objects.exclude(rule__isnull=True).exclude(rule='')
    
    problemas = []
    for obj in objetos:
        try:
            rule_engine.Rule(obj.rule)
            print(f"✓ OK: {obj.id} - {obj.rule[:50]}")
        except Exception as e:
            print(f"✗ ERRO: {obj.id} - {str(e)}")
            problemas.append({
                'id': obj.id,
                'rule': obj.rule,
                'error': str(e)
            })
    
    if problemas:
        print(f"\n{len(problemas)} regras com problemas:")
        for p in problemas:
            print(f"  ID {p['id']}: {p['error']}")
    else:
        print(f"\n✓ Todas as {objetos.count()} regras são válidas!")

if __name__ == "__main__":
    validar_regras()
```

Execute:
```bash
python manage.py shell < validate_existing_rules.py
```

---

## 2. Aplicar em Outro Projeto

Para usar o RuleField em outro projeto Django:

### Opção A: Copiar Módulo Completo

1. **Copiar arquivos:**
```bash
# Do projeto fonte
cp -r src/base/fields /caminho/destino/seu_app/

# Copiar templates
cp -r src/base/templates/widgets /caminho/destino/seu_app/templates/

# Copiar static
cp -r src/base/static/rule_widget /caminho/destino/seu_app/static/

# Copiar API
cp -r src/base/api /caminho/destino/seu_app/
```

2. **Ajustar imports:**

Em `seu_app/fields/__init__.py`:
```python
from .rule_field import RuleField
__all__ = ["RuleField"]
```

3. **Configurar URLs:**

No `urls.py` principal:
```python
from django.urls import path, include

urlpatterns = [
    # ... outras URLs
    path("api/", include("seu_app.api.urls")),
]
```

4. **Instalar dependências:**
```bash
pip install rule-engine==4.5.3 jsonschema==4.26.0
```

5. **Coletar estáticos:**
```bash
python manage.py collectstatic --noinput
```

### Opção B: Criar Pacote Reutilizável

Crie um pacote Python separado:

```
django-rule-field/
├── setup.py
├── README.md
├── django_rule_field/
│   ├── __init__.py
│   ├── fields.py
│   ├── widgets.py
│   ├── views.py
│   ├── urls.py
│   ├── templates/
│   └── static/
└── tests/
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name='django-rule-field',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=5.0',
        'rule-engine>=4.5.0',
        'jsonschema>=4.0.0',
    ],
    # ... mais configurações
)
```

Instalar em qualquer projeto:
```bash
pip install /caminho/para/django-rule-field
```

---

## 3. Customizar para Necessidades Específicas

### 3.1. Customizar Tema do Editor

No `rule_widget.html`, altere o tema:

```html
<!-- Trocar de 'monokai' para outro tema -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.16/theme/dracula.min.css">

<!-- No JavaScript -->
CodeMirror.fromTextArea(textarea, {
    theme: 'dracula',  // ao invés de 'monokai'
    // ... outras opções
});
```

Temas disponíveis:
- `monokai` (padrão)
- `dracula`
- `material`
- `solarized`
- `eclipse`
- `idea`

### 3.2. Adicionar Funções Customizadas

Criar resolver customizado:

```python
# seu_app/resolvers.py
import rule_engine

custom_resolver = rule_engine.Resolver()

@custom_resolver.register_function
def is_valid_cpf(cpf):
    """Valida CPF brasileiro."""
    # Lógica de validação
    return True  # simplificado

@custom_resolver.register_function
def is_email_institucional(email):
    """Verifica se é email institucional."""
    return '@ifrn.edu.br' in email or '@edu.br' in email
```

Usar no modelo:

```python
from seu_app.resolvers import custom_resolver

class MeuModelo(models.Model):
    rule = RuleField(
        resolver=custom_resolver,
        example_data={"cpf": "123.456.789-00", "email": "user@ifrn.edu.br"}
    )
```

Agora pode usar nas regras:
```
is_valid_cpf(cpf) and is_email_institucional(email)
```

### 3.3. Customizar Validação

Criar campo especializado:

```python
from django_rule_engine.fields import RuleField
import rule_engine

class StrictRuleField(RuleField):
    """RuleField com validação mais rigorosa."""
    
    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        
        if not value:
            return
        
        # Validação customizada
        if 'eval(' in value or 'exec(' in value:
            raise ValidationError(
                'Funções eval() e exec() não são permitidas',
                code='unsafe_function'
            )
        
        # Limitar complexidade
        if value.count('and') + value.count('or') > 10:
            raise ValidationError(
                'Regra muito complexa (máximo 10 operadores)',
                code='too_complex'
            )
```

### 3.4. Adicionar Autocomplete

Modificar `rule_widget.js` para adicionar sugestões:

```javascript
// No método initCodeMirror()
this.ruleEditor = CodeMirror.fromTextArea(this.ruleTextarea, {
    mode: 'python',
    theme: 'monokai',
    // ... outras opções
    
    // Adicionar autocomplete
    extraKeys: {
        'Ctrl-Space': 'autocomplete',
        'Ctrl-Enter': () => this.validateRule()
    },
    
    // Sugestões customizadas
    hintOptions: {
        hint: (cm) => {
            const cursor = cm.getCursor();
            const token = cm.getTokenAt(cursor);
            const list = [
                'login', 'email', 'nome', 'status',
                'idade', 'nivel', 'ativo',
                'len()', 'abs()', 'max()', 'min()',
                'and', 'or', 'not', 'in'
            ];
            
            return {
                list: list.filter(item => item.startsWith(token.string)),
                from: CodeMirror.Pos(cursor.line, token.start),
                to: CodeMirror.Pos(cursor.line, token.end)
            };
        }
    }
});
```

### 3.5. Suportar Múltiplos Idiomas

Criar versão internacionalizada:

```python
# base/fields/i18n_rule_field.py
from django.utils.translation import gettext_lazy as _
from .rule_field import RuleField

class I18nRuleField(RuleField):
    """RuleField com suporte a i18n."""
    
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('verbose_name', _('Rule'))
        kwargs.setdefault('help_text', _('Enter a valid rule-engine expression'))
        super().__init__(*args, **kwargs)
```

Traduzir strings no template e JavaScript.

---

## 4. Rollback/Reversão

Se precisar voltar para TextField simples:

### Passo 1: Backup

```bash
python manage.py dumpdata seu_app.SeuModelo > backup_antes_rollback.json
```

### Passo 2: Reverter Modelo

```python
class Cohort(models.Model):
    name = CharField("cohort name", max_length=2560, unique=True)
    rule = TextField("regra", blank=True, null=True)
```

### Passo 3: Criar Migration de Reversão

```bash
python manage.py makemigrations
```

### Passo 4: Aplicar

```bash
python manage.py migrate
```

### Passo 5: Remover Dependências (opcional)

```bash
# Remover módulos
rm -rf base/fields/
rm -rf base/api/
rm -rf base/templates/widgets/rule_widget.html
rm -rf base/static/rule_widget/

# Remover da URLs
# Editar urls.py e remover linha: path("api/", include("base.api.urls")),
```

---

## 5. Troubleshooting de Migração

### Erro: "No module named 'django_rule_engine.fields'"

**Solução:**
1. Verifique se `base/fields/__init__.py` existe
2. Certifique-se de que está no PYTHONPATH
3. Reinicie o servidor Django

### Erro: "Table doesn't exist"

**Solução:**
```bash
python manage.py migrate --run-syncdb
```

### Erro: "Static files not found"

**Solução:**
```bash
python manage.py collectstatic --clear --noinput
```

### Erro: "API endpoint 404"

**Solução:**
1. Verifique se URL foi adicionada em `urls.py`
2. Verifique namespace correto
3. Teste endpoint: `curl -X POST http://localhost:8000/api/validate-rule/`

---

## 6. Checklist de Migração

Antes de considerar a migração completa, verifique:

- [ ] Backup do banco de dados criado
- [ ] Todos os arquivos copiados
- [ ] Dependencies instaladas (`requirements.txt`)
- [ ] Migrations criadas e aplicadas
- [ ] Static files coletados
- [ ] URLs configuradas
- [ ] Testes executados com sucesso
- [ ] Regras existentes validadas
- [ ] Admin funciona corretamente
- [ ] API responde corretamente
- [ ] Documentação atualizada

---

## 7. Recursos Adicionais

- [Documentação rule-engine](https://zerosteiner.github.io/rule-engine/)
- [Django Custom Fields](https://docs.djangoproject.com/en/stable/howto/custom-model-fields/)
- [CodeMirror Documentation](https://codemirror.net/doc/manual.html)

---

**Criado para facilitar a migração e customização do RuleField** 🚀
