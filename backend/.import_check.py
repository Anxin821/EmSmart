import importlib, sys
modules = ['app.services.production_service','app.api.v1.routers.production','app.repositories.production_repository']
print('PYIMPORTCHECK_START')
for m in modules:
    try:
        importlib.import_module(m)
        print('OK:', m)
    except Exception:
        print('ERROR:', m)
        import traceback
        traceback.print_exc()
        sys.exit(2)
print('PYIMPORTCHECK_OK')
