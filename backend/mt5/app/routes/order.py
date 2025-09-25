from flask import Blueprint, jsonify, request
import MetaTrader5 as mt5
import logging
from flasgger import swag_from
from routes.auth import require_auth  # ✅ Importar middleware

order_bp = Blueprint('order', __name__)
logger = logging.getLogger(__name__)

@order_bp.route('/order', methods=['POST'])
@require_auth  # ✅ Añadir protección
@swag_from({
    'tags': ['Order'],
    'security': [{'ApiKeyAuth': []}],  # ✅ Actualizar Swagger
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'symbol': {'type': 'string'},
                    'volume': {'type': 'number'},
                    'type': {'type': 'string', 'enum': ['BUY', 'SELL']},
                    'deviation': {'type': 'integer', 'default': 20},
                    'magic': {'type': 'integer', 'default': 0},
                    'comment': {'type': 'string', 'default': ''},
                    'type_filling': {'type': 'string', 'enum': ['ORDER_FILLING_IOC', 'ORDER_FILLING_FOK', 'ORDER_FILLING_RETURN']},
                    'sl': {'type': 'number'},
                    'tp': {'type': 'number'}
                },
                'required': ['symbol', 'volume', 'type']
            }
        }
    ],
    'responses': {
        200: {
            'description': 'Order executed successfully.',
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
            'description': 'Bad request or order failed.'
        },
        500: {
            'description': 'Internal server error.'
        }
    }
})
def send_market_order_endpoint():
    """
    Send Market Order
    ---
    description: Execute a market order for a specified symbol with optional parameters.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Order data is required"}), 400

        required_fields = ['symbol', 'volume', 'type']
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400

        # Prepare the order request
        request_data = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": data['symbol'],
            "volume": float(data['volume']),
            "type": data['type'],
            "deviation": data.get('deviation', 20),
            "magic": data.get('magic', 0),
            "comment": data.get('comment', ''),
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": data.get('type_filling', mt5.ORDER_FILLING_IOC),
        }

        # Get current price
        tick = mt5.symbol_info_tick(data['symbol'])
        if tick is None:
            return jsonify({"error": "Failed to get symbol price"}), 400

        # Set price based on order type
        if data['type'] == mt5.ORDER_TYPE_BUY:
            request_data["price"] = tick.ask
        elif data['type'] == mt5.ORDER_TYPE_SELL:
            request_data["price"] = tick.bid
        else:
            return jsonify({"error": "Invalid order type"}), 400

        # Add optional SL/TP if provided
        if 'sl' in data:
            request_data["sl"] = data['sl']
        if 'tp' in data:
            request_data["tp"] = data['tp']

        # Send order
        result = mt5.order_send(request_data)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            error_code, error_str = mt5.last_error()
            
            return jsonify({
                "error": f"Order failed: {result.comment}",
                "mt5_error": error_str,
                "result": result._asdict()
            }), 400

        return jsonify({
            "message": "Order executed successfully",
            "result": result._asdict()
        })
    
    except Exception as e:
        logger.error(f"Error in send_market_order: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500