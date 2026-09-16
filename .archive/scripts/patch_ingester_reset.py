with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    ing = f.read()

target = '''if cmd not in ['enable_valve', 'disable_valve', 'identify', 'trigger_siren', 'force_update']:'''
replace = '''if cmd not in ['enable_valve', 'disable_valve', 'identify', 'trigger_siren', 'force_update', 'factory_reset']:'''

if "factory_reset" not in target and "factory_reset" not in ing:
    ing = ing.replace(target, replace)
    with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
        f.write(ing)
