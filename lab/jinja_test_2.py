from jinja2 import Template

template_str = """
{% for item in items %}
    {{ item }} → {{ lookup_table.get(item, 'Unknown') }}
{% endfor %}
"""

template = Template(template_str)
data = {
    "lookup_table": {"apple": "fruit", "carrot": "vegetable", "chicken": "meat"},
    "items": ["apple", "carrot", "banana", "your mom"]
}

print(template.render(data))
