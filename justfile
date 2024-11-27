project := file_stem(justfile_dir())
venv-name := ".venv"
venv-path := join(justfile_dir(), venv-name)
pip-cmd := shell('if [ -x "$(command -v uv)" ]; then echo "uv pip"; else echo "pip"; fi')

# ==============================================================================
# DJANGO RECIPES
# ==============================================================================

# Launch development server
r: check-venv
    ./manage.py runserver

# Launch Django interactive shell
sh: check-venv
    ./manage.py shell

alias mm := makemigrations
# Make Django migrations
makemigrations: check-venv
    ./manage.py makemigrations
    
alias m := migrate
# Apply Django migrations
migrate: check-venv
    ./manage.py migrate

# Check if Django project is correct
check: check-venv
    ./manage.py check

# Add a new app and install it on settings.py
startapp app: check-venv
    #!/usr/bin/env bash
    python manage.py startapp {{ app }}
    APP_CLASS={{ app }}
    APP_CONFIG="{{ app }}.apps.${APP_CLASS^}Config"
    perl -0pi -e "s/(INSTALLED_APPS *= *\[)(.*?)(\])/\1\2    '$APP_CONFIG',\n\3/smg" ./main/settings.py
    echo "✔ {{ app }} installed & added to settings.INSTALLED_APPS"

# ==============================================================================
# VIRTUALENV RECIPES
# ==============================================================================

# Create a Python virtualenv
create-venv:
    #!/usr/bin/env bash
    if [ ! -d {{ venv-name }} ]
    then
        if [ -x "$(command -v uv)" ]
        then
            uv venv --seed
        else
            python -m venv {{ venv-name }} --prompt {{ project }}
        fi
    fi

# Check if Python virtualenv is activated
[private]
[no-exit-message]
check-venv: create-venv
    #!/usr/bin/env bash
    if [ "$VIRTUAL_ENV" != "{{ venv-path }}" ]; then
        echo Project virtualenv: {{ venv-path }}
        echo Active virtualenv: $VIRTUAL_ENV
        echo
        echo You must activate the right virtualenv!
        exit 1
    fi

# Install project requirements
install-reqs: check-venv
    {{ pip-cmd }} install -r requirements.txt

# ==============================================================================
# DJANGO AUX RECIPES
# ==============================================================================

# Setup a Django project
setup: install-reqs && migrate create-su
    #!/usr/bin/env bash
    django-admin startproject main .
    sed -i -E "s/(TIME_ZONE).*/\1 = 'Atlantic\/Canary'/" ./main/settings.py
    echo "✔ Fixed TIME_ZONE='Atlantic/Canary' and LANGUAGE_CODE='es-es'"

# Generate fake data and populate Django database
[private]
@gen-data *args: check-venv
    #!/usr/bin/env bash
    ./manage.py gen_data {{ args }}

# Dump fixtures
[private]
dump-data: gen-data
    ./manage.py dumpdata --format json --indent 2 auth -o fixtures/auth.json
    ./manage.py dumpdata --format json --indent 2 slots -o fixtures/slots.json
    ./manage.py dumpdata --format json --indent 2 appointments -o fixtures/appointments.json

# Load fixtures into database
load-data: check-venv
    #!/usr/bin/env bash
    ./manage.py loaddata fixtures/auth.json
    ./manage.py loaddata fixtures/slots.json
    ./manage.py loaddata fixtures/appointments.json
    echo --------------------------------
    ./manage.py shell -c '
    from django.contrib.auth.models import User
    print("Available users (with password 1234)\n")
    for user in User.objects.exclude(is_superuser=True):
        print(user)
    '

# Create a superuser (or update it if already exists)
create-su username="admin" password="admin" email="admin@example.com":
    #!/usr/bin/env bash
    ./manage.py shell -c '
    from django.contrib.auth.models import User
    user, _ = User.objects.get_or_create(username="{{ username }}")
    user.email = "{{ email }}"
    user.set_password("{{ password }}") 
    user.is_superuser = True
    user.is_staff = True
    user.save()
    ' 
    echo "✔ Created superuser → {{ username }}:{{ password }}"

# https://medium.com/@mustahibmajgaonkar/how-to-reset-django-migrations-6787b2a1e723
# https://stackoverflow.com/a/76300128
# Remove migrations and database. Reset DB artefacts.
[confirm("⚠️ All migrations and database will be removed. Continue? [yN]:")]
reset-db: && create-su
    #!/usr/bin/env bash
    find . -path "*/migrations/*.py" ! -path "./.venv/*" ! -name "__init__.py" -delete
    find . -path "*/migrations/*.pyc" ! -path "./.venv/*" -delete
    rm -f db.sqlite3
    ./manage.py makemigrations
    ./manage.py migrate
    echo

# ==============================================================================
# MISC RECIPES
# ==============================================================================

# Enable testing with pytest inside VSCode
enable-vscode-pytest:
    #!/usr/bin/env bash
    mkdir -p .vscode
    cat << EOF > .vscode/settings.json
    {
      "python.testing.pytestArgs": ["tests"],
      "python.testing.unittestEnabled": false,
      "python.testing.pytestEnabled": true
    }
    EOF