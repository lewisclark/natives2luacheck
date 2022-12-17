import requests

natives = requests.get("https://runtime.fivem.net/doc/natives.json")
cfx_natives = requests.get("https://runtime.fivem.net/doc/natives_cfx.json")

def luaify_name(name):
    parts = []

    for word in name.strip().lower().split("_"):
        if not word:
            continue

        parts.append(word[0].upper() + word[1:])

    return "".join(parts)

def parse_json(j):
    clean_funcs = []

    for category in j:
        for func in j[category]:
            func_data = j[category][func]

            name = func_data.get("name")

            if not name:
                continue

            realm = func_data.get("apiset", "shared")

            clean_funcs.append(
                {
                    "name": luaify_name(name),
                    "realm": realm
                }
            )

    return clean_funcs

def separate_per_realm(funcs):
    cl, sv, sh = [], [], []

    for func in funcs:
        realm = func["realm"]

        if realm == "client":
            cl.append(func)
        elif realm == "server":
            sv.append(func)
        elif realm == "shared":
            sh.append(func)

    return cl, sv, sh

def dedup(client_funcs, server_funcs, shared_funcs):
    for shfunc in shared_funcs:
        for clfunc in client_funcs:
            if shfunc["name"] == clfunc["name"]:
                client_funcs.remove(clfunc)
                break

        for svfunc in server_funcs:
            if shfunc["name"] == svfunc["name"]:
                server_funcs.remove(svfunc)
                break

    removed_client_funcs = []
    for clfunc in client_funcs:
        for svfunc in server_funcs:
            if clfunc["name"] == svfunc["name"]:
                server_funcs.remove(svfunc)
                removed_client_funcs.append(clfunc)
                shared_funcs.append(clfunc)
                break

    for clfunc in removed_client_funcs:
        client_funcs.remove(clfunc)

def make_lua_table(funcs, tname):
    lua_names = []

    for func in funcs:
        name = func["name"]
        lua_names.append(f"\t\"{name}\",")

    joined = "\n".join(lua_names)

    return f"local {tname} = {{\n{joined}\n}}"

clean_natives = parse_json(natives.json())
clean_natives.extend(parse_json(cfx_natives.json()))

client, server, shared = separate_per_realm(clean_natives)
dedup(client, server, shared)

print(f"{len(client)} clfuncs, {len(server)} svfuncs, {len(shared)} shfuncs")

with open("out.lua", "w", encoding="utf8") as f:
    client_out = make_lua_table(client, "globals_client")
    server_out = make_lua_table(server, "globals_server")
    shared_out = make_lua_table(shared, "globals_shared")

    print(f"{client_out}\n\n{server_out}\n\n{shared_out}", file=f)
