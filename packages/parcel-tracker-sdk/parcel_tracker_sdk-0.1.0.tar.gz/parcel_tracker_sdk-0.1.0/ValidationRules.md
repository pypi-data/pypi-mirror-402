# Validation Rules

## Tenants
- Id2(ExternalId) optional non-empty
- FirstName mandatory length >= 1
- LastName mandatory length >= 0
- Email mandatory validated for its format
- Phone optional, if the format is not all digits, try to adjust it so that e.g. "(+44) 079 999 99999" is sent to the API as 447999999999
- Room(Location) mandatory, length > 0
- Alias optional
- DevelopmentId integer mandatory
