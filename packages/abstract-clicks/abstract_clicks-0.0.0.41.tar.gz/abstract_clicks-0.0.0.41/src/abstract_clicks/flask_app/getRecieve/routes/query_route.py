from abstract_flask import *
from ..imports import *
query_bp,logger = get_bp('query_bp',__name__,
                         url_prefix=URL_PREFIX,
                         static_folder=QUERY_DIR)
@query_bp.route('/query',methods=["POST","GET"])
def QuErY():
    data = parse_and_spec_vars(request,['query'])
    query = data.get('query')
    logger.info(f"qury  == {query}")
    safe_dump_to_file(data=query,file_path=QUERY_FILE_PATH)
    return jsonify({"result":True}), 200
