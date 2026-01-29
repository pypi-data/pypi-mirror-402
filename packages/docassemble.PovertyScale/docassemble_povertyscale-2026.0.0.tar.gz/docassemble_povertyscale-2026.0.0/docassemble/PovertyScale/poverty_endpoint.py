# pre-load

from flask import jsonify, request, Response
from docassemble.webapp.app_object import app

from .poverty import get_poverty_scale_data, poverty_scale_get_income_limit, poverty_scale_income_qualifies


@app.route("/poverty_guidelines", methods=['GET'])
def get_poverty_guidelines():
  results = get_poverty_scale_data()
  if results:
    return jsonify(results)
  else:
    return Response('{"error": "Unable to load poverty guidelines from disk."}', status=503, mimetype="application/json")

@app.route("/poverty_guidelines/household_size/<household_size>", methods=['GET'])
def get_household_poverty_guideline(household_size:int):
  if (request.args) and str(request.args.get('state')).lower() in ['ak','hi']:
    state = str(request.args.get('state')).lower()
  else:
    state = None
  if (request.args) and request.args.get('multiplier'):
    try:      
      multiplier = float(request.args.get('multiplier', 1.0))
    except :
      multiplier = 1.0
  else:
    multiplier = 1.0
  results = poverty_scale_get_income_limit(int(household_size), multiplier=multiplier, state=state)
  ps_data = get_poverty_scale_data()
  if isinstance(ps_data, dict):
    update_year = ps_data.get('poverty_level_update_year')
  else:
    update_year = -1
  if results:
    return jsonify({'amount': results, 'update_year': update_year})
  else:
    return Response('{"error": "Unable to retrieve poverty guidelines."}', status=503, mimetype="application/json")

@app.route("/poverty_guidelines/qualifies/household_size/<household_size>", methods=['GET'])
def get_household_qualifies(household_size:int):
  if not request.args or not 'income' in request.args:
    return Response('{"error": "Income is required"}', 400, mimetype="application/json")
  try:
    income = int(request.args['income'])
  except ValueError:
    return Response('{"error": "Invalid income value. Please provide an integer."}', 400, mimetype="application/json")
  if str(request.args.get('state')).lower() in ['ak','hi']:
    state = str(request.args.get('state')).lower()
  else:
    state = None
  if 'multiplier' in request.args:
    try:      
      multiplier = float(request.args['multiplier'])
    except :
      multiplier = 1.0
  else:
    multiplier = 1.0
  results = poverty_scale_income_qualifies(income, int(household_size), multiplier=multiplier, state=state)
  ps_data = get_poverty_scale_data()
  if isinstance(ps_data, dict):
    update_year = ps_data.get('poverty_level_update_year')
  else:
    update_year = -1
  if not results is None:
    return jsonify({'qualifies': results, 'update_year': update_year})
  else:
    return Response('{"error": "Unable to retrieve poverty guidelines."}', status=503, mimetype="application/json")
  