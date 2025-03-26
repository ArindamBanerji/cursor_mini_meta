# Template Integration Plan

Based on our analysis of the controllers and session middleware implementation, the following template updates are needed:

## 1. Create Layout Template with Flash Messages Support

A base layout template (`templates/layout.html`) should be created with support for flash messages:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SAP Test Harness{% endblock %}</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Custom styles -->
    <link href="{{ url_for('static', path='/css/styles.css') }}" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">SAP Test Harness</a>
            <!-- Navigation elements here -->
        </div>
    </nav>

    <div class="container my-4">
        <!-- Flash messages -->
        {% if flash_messages %}
            {% for message in flash_messages %}
                <div class="alert {{ message.bootstrap_class }} alert-dismissible fade show" role="alert">
                    {{ message.message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}
        <!-- Content goes here -->
        {% endblock %}
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Custom scripts -->
    <script src="{{ url_for('static', path='/js/main.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

## 2. Update Form Templates to Use Session Data

Each form template should be updated to use session data for:
1. Pre-filling form fields with previous input when validation errors occur
2. Displaying validation errors

Example form template updates:

```html
<!-- Input field with error handling -->
<div class="mb-3">
    <label for="name" class="form-label">Name</label>
    <input type="text" class="form-control {% if errors and 'name' in errors %}is-invalid{% endif %}" 
           id="name" name="name" value="{{ form_data.name if form_data and 'name' in form_data else '' }}">
    {% if errors and 'name' in errors %}
        <div class="invalid-feedback">{{ errors.name }}</div>
    {% endif %}
</div>
```

## 3. Template Files to Update

Based on the controllers we've updated, these templates need modifications:

### Material Templates
- `templates/material/list.html` - Add flash messages
- `templates/material/detail.html` - Add flash messages
- `templates/material/create.html` - Add form data preservation and validation errors
- `templates/material/edit.html` - Add form data preservation and validation errors

### P2P Requisition Templates
- `templates/requisition/list.html` - Add flash messages
- `templates/requisition/detail.html` - Add flash messages
- `templates/requisition/create.html` - Add form data preservation and validation errors
- `templates/requisition/edit.html` - Add form data preservation and validation errors

### P2P Order Templates
- `templates/order/list.html` - Add flash messages
- `templates/order/detail.html` - Add flash messages
- `templates/order/create.html` - Add form data preservation and validation errors
- `templates/order/edit.html` - Add form data preservation and validation errors

## Implementation Approach

1. Create the base layout template with flash message support first
2. Create reusable form macros for common form elements with error handling
3. Update form templates to use the form macros and session data
4. Ensure all templates extend the base layout template 