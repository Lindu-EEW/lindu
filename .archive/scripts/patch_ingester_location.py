with open('prototype/grafana-stack/ingester/ingester.py', 'r') as f:
    ing = f.read()

target_whitelist = '''if cmd not in ['enable_valve', 'disable_valve', 'identify', 'trigger_siren', 'force_update', 'factory_reset']:'''
replace_whitelist = '''if cmd not in ['enable_valve', 'disable_valve', 'identify', 'trigger_siren', 'force_update', 'factory_reset', 'set_location']:'''

target_payload = '''payload = {"cmd": cmd, "target_node": target}'''
replace_payload = '''payload = {"cmd": cmd, "target_node": target}
        if cmd == "set_location":
            payload["lat"] = float(data.get("lat", 0.0))
            payload["lon"] = float(data.get("lon", 0.0))'''

if "set_location" not in target_whitelist and "set_location" not in ing:
    ing = ing.replace(target_whitelist, replace_whitelist)
    ing = ing.replace(target_payload, replace_payload)
    with open('prototype/grafana-stack/ingester/ingester.py', 'w') as f:
        f.write(ing)
