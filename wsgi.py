import ssl
from waitress import serve
from app import app  # Import your Flask app instance

if __name__ == "__main__":
    print("Starting the Waitress server...")
    
    # Create SSL context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
    
    # Create a simple HTTP server
    from waitress import create_server
    server = create_server(app, host="0.0.0.0", port=8080)
    
    # Wrap the server with SSL
    server.ssl_context = context

    # Start the server
    print("Server started on https://0.0.0.0:8080")
    server.serve_forever()
