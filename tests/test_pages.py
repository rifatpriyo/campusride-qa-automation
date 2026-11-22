def test_health_and_local_swagger_assets(client):
    assert client.get("/health").json() == {"status": "ok"}
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "/static-offline-docs/swagger-ui-bundle.js" in docs.text
    assert client.get("/static-offline-docs/swagger-ui-bundle.js").status_code == 200
    schema = client.get("/openapi.json").json()
    assert "/api/rides/quote" in schema["paths"]
    assert schema["components"]["securitySchemes"]["CampusRideSession"]["in"] == "cookie"


def test_pages_render_with_stable_controls_and_permissions(client, sign_in):
    assert client.get("/passenger", follow_redirects=False).headers["location"] == "/login"
    assert 'data-testid="demo-passenger"' in client.get("/login").text
    assert 'data-testid="register-submit"' in client.get("/register").text
    passenger, rider, admin = (sign_in(key) for key in ("mira", "anika", "admin"))
    pages = [
        (passenger, "/passenger", "book-ride"),
        (passenger, "/book", "get-fare"),
        (passenger, "/rides/1", "received-rating"),
        (rider, "/rider", "accept-ride"),
        (admin, "/admin", "approve-rider"),
    ]
    for viewer, path, test_id in pages:
        page = viewer.get(path)
        assert page.status_code == 200, page.text
        assert f'data-testid="{test_id}"' in page.text
    assert rider.get("/rides/7").status_code == 404
    assert passenger.get("/admin").status_code == 403
