import pytest

from faker import Faker

from db_anonymiser import faker as db_anonymiser_faker


# Force faker to use a seed when producing output so that we can assume a
# deterministic set of results
@pytest.fixture(autouse=True)
def seed_faker():
    Faker.seed(0)


def test_sanitize_name():
    assert db_anonymiser_faker.sanitize_name("Bob Benson") == "Dr Rhys Thomas"


def test_sanitize_first_name():
    assert db_anonymiser_faker.sanitize_first_name("Bob") == "Emma"


def test_sanitize_last_name():
    assert db_anonymiser_faker.sanitize_last_name("Benson") == "Watts"


def test_sanitize_email():
    assert (
        db_anonymiser_faker.sanitize_email("bob.benson@example.net")
        == "areed@example.org"
    )


def test_sanitize_company_name():
    assert db_anonymiser_faker.sanitize_company_name("Sterling Cooper") == "Reed-Burton"


def test_sanitize_phone_number():
    assert db_anonymiser_faker.sanitize_phone_number("011111111111") == "+448764759382"


def test_sanitize_address():
    assert (
        db_anonymiser_faker.sanitize_address("Madison Ave")
        == "Flat 4, Gibbons tunnel, Lesleystad, L8C 2EZ"
    )


def test_sanitize_website():
    assert (
        db_anonymiser_faker.sanitize_website("sterling.cooper")
        == "reed-burton.arnold-jones.com"
    )


def test_sanitize_text():
    assert (
        db_anonymiser_faker.sanitize_text("Not great, Bob.")
        == "Aliquam vitae laborum ullam rerum voluptas. Nesciunt tenetur magnam eligendi quidem nulla. Voluptates minus provident nobis corporis. Quas tempore placeat iusto. Explicabo et odit dignissimos."
    )
    assert db_anonymiser_faker.sanitize_text(None) == None


def test_sanitize_street_address():
    assert (
        db_anonymiser_faker.sanitize_street_address("Madison Ave")
        == "Studio 0\nArnold oval"
    )


def test_sanitize_city():
    assert db_anonymiser_faker.sanitize_city("New York") == "Reedchester"


def test_sanitize_postcode():
    assert db_anonymiser_faker.sanitize_postcode("DT11 7DY") == "TA60 8UR"


def test_sanitize_eori_number():
    assert (
        db_anonymiser_faker.sanitize_eori_number("GB111111111111") == "GB424533559245"
    )


def test_sanitize_ni_eori_number():
    assert (
        db_anonymiser_faker.sanitize_ni_eori_number("XI111111111111") == "XI424533559245"
    )

def test_sanitize_eu_eori_number():
    assert (
        db_anonymiser_faker.sanitize_eu_eori_number("FR11111") == "FR99346"
    )

def test_sanitize_sic_number():
    assert db_anonymiser_faker.sanitize_sic_number("11111") == "50494"


def test_sanitize_vat_number():
    assert db_anonymiser_faker.sanitize_vat_number("GB111111111") == "GB906691059"


def test_sanitize_registration_number():
    assert db_anonymiser_faker.sanitize_registration_number("11111111") == "51706749"


def test_sanitize_filename():
    assert db_anonymiser_faker.sanitize_filename("somefile.txt") == "molestiae.xlsx"


def test_sanitize_short_text():
    assert (
        db_anonymiser_faker.sanitize_short_text("some small text")
        == "Tempore placeat iusto aut. Et odit dignissimos mollitia ipsam maxime."
    )
    assert db_anonymiser_faker.sanitize_short_text(None) == None
