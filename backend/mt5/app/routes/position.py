from flask import Blueprint, jsonify, request
import MetaTrader5 as mt5
import logging
from lib import close_position, close_all_positions, get_positions
from flasgger import swag_from
from routes.auth import require_auth  # ✅ Importar middleware

position_bp = Blueprint('position', __name__)
logger = logging.getLogger(__name__)

@position_bp.route('/close_position', methods=['POST'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Position'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'position': {
                        'type': 'object',
                        'properties': {
                            'type': {'type': 'integer'},
                            'ticket': {'type': 'integer'},
                            'symbol': {'type': 'string'},
                            'volume': {'type': 'number'}
                        },
                        'required': ['type', 'ticket', 'symbol', 'volume']
                    }
                },
                'required': ['position']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Position closed successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'result': {
                        'type': 'object',
                        'properties': {
                            'retcode': {'type': 'integer'},
                            'order': {'type': 'integer'},
                            'magic': {'type': 'integer'},
                            'price': {'type': 'number'},
                            'symbol': {'type': 'string'},
                            # Add other relevant fields as needed
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request or failed to close position.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def close_position_endpoint():
    """
    Close a Specific Position
    ---
    description: Close a specific trading position based on the provided position data.
    """
    try:
        data = request.get_json()
        if not data or 'position' not in data:
            return jsonify({"error": "Position data is required"}), 400
        
        result = close_position(data['position'])
        if result is None:
            return jsonify({"error": "Failed to close position"}), 400
        
        return jsonify({"message": "Position closed successfully", "result": result._asdict()})
    
    except Exception as e:
        logger.error(f"Error in close_position: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@position_bp.route('/close_all_positions', methods=['POST'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Position'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': False,
            'schema': {
                'type': 'object',
                'properties': {
                    'order_type': {'type': 'string', 'enum': ['BUY', 'SELL', 'all'], 'default': 'all'},
                    'magic': {'type': 'integer'}
                }
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Closed positions successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'retcode': {'type': 'integer'},
                                'order': {'type': 'integer'},
                                'magic': {'type': 'integer'},
                                'price': {'type': 'number'},
                                'symbol': {'type': 'string'},
                                # Add other relevant fields as needed
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request or no positions were closed.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def close_all_positions_endpoint():
    """
    Close All Positions
    ---
    description: Close all open trading positions based on optional filters like order type and magic number.
    """
    try:
        data = request.get_json() or {}
        order_type = data.get('order_type', 'all')
        magic = data.get('magic')
        
        results = close_all_positions(order_type, magic)
        if not results:
            return jsonify({"message": "No positions were closed"}), 200
        
        return jsonify({
            "message": f"Closed {len(results)} positions",
            "results": [result._asdict() for result in results]
        })
    
    except Exception as e:
        logger.error(f"Error in close_all_positions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@position_bp.route('/modify_sl_tp', methods=['POST'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Position'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'position': {'type': 'integer'},
                    'sl': {'type': 'number'},
                    'tp': {'type': 'number'}
                },
                'required': ['position']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'SL/TP modified successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'result': {
                        'type': 'object',
                        'properties': {
                            'retcode': {'type': 'integer'},
                            'order': {'type': 'integer'},
                            'magic': {'type': 'integer'},
                            'price': {'type': 'number'},
                            'symbol': {'type': 'string'},
                            # Add other relevant fields as needed
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request or failed to modify SL/TP.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def modify_sl_tp_endpoint():
    """
    Modify Stop Loss and Take Profit
    ---
    description: Modify the Stop Loss (SL) and Take Profit (TP) levels for a specific position.
    """
    try:
        data = request.get_json()
        if not data or 'position' not in data:
            return jsonify({"error": "Position data is required"}), 400
        
        position = data['position']
        sl = data.get('sl')
        tp = data.get('tp')
        
        request_data = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position,
            "sl": sl,
            "tp": tp
        }
        
        result = mt5.order_send(request_data)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return jsonify({"error": f"Failed to modify SL/TP: {result.comment}"}), 400
        
        return jsonify({"message": "SL/TP modified successfully", "result": result._asdict()})
    
    except Exception as e:
        logger.error(f"Error in modify_sl_tp: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@position_bp.route('/get_positions', methods=['GET'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Position'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'parameters': [
        {
            'name': 'magic',
            'in': 'query',
            'type': 'integer',
            'required': False,
            'description': 'Magic number to filter positions.'
        }
    ],
    'responses': {
        200: {
            'description': 'Positions retrieved successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'positions': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'ticket': {'type': 'integer'},
                                'time': {'type': 'string', 'format': 'date-time'},
                                'type': {'type': 'integer'},
                                'magic': {'type': 'integer'},
                                'symbol': {'type': 'string'},
                                'volume': {'type': 'number'},
                                'price_open': {'type': 'number'},
                                'sl': {'type': 'number'},
                                'tp': {'type': 'number'},
                                'price_current': {'type': 'number'},
                                'swap': {'type': 'number'},
                                'profit': {'type': 'number'},
                                'comment': {'type': 'string'},
                                'external_id': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        },
        400: {
            'description': 'Bad request or failed to retrieve positions.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def get_positions_endpoint():
    """
    Get Open Positions
    ---
    description: Retrieve all open trading positions, optionally filtered by magic number.
    """
    try:
        magic = request.args.get('magic', type=int)

        positions_df = get_positions(magic)

        if positions_df is None:
            return jsonify({"error": "Failed to retrieve positions"}), 500
            
        if positions_df.empty:
            return jsonify({"positions": []}), 200
            
        return jsonify(positions_df.to_dict(orient='records')), 200
    
    except Exception as e:
        logger.error(f"Error in get_positions: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@position_bp.route('/positions_total', methods=['GET'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Position'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'responses': {
        200: {
            'description': 'Total number of open positions retrieved successfully.',
            'schema': {
                'type': 'object',
                'properties': {
                    'total': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Failed to get positions total.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def positions_total_endpoint():
    """
    Get Total Open Positions
    ---
    description: Retrieve the total number of open trading positions.
    """
    try:
        total = mt5.positions_total()
        if total is None:
            return jsonify({"error": "Failed to get positions total"}), 400
        
        return jsonify({"total": total})
    
    except Exception as e:
        logger.error(f"Error in positions_total: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500