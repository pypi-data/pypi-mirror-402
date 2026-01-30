"""
Configuration du logging
"""

import logging
from flask import request
import time


def setup_logging(app):
    """Configurer le logging pour l'application"""
    
    # Configuration du logger
    logging.basicConfig(
        level=logging.INFO if app.debug else logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('bmb')
    
    @app.before_request
    def log_request():
        """Logger chaque requête"""
        request.start_time = time.time()
        logger.info(f"⮕  {request.method} {request.path}")
    
    @app.after_request
    def log_response(response):
        """Logger chaque réponse"""
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(
                f"⮐  {request.method} {request.path} "
                f"- Status: {response.status_code} "
                f"- Duration: {duration:.3f}s"
            )
        return response
    
    return logger