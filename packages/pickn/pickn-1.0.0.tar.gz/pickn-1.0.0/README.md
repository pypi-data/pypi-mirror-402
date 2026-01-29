# Pickn Python SDK

SDK officiel pour l'API Pickn - Paiements et livraisons

## Installation

```bash
pip install pickn
```

## Usage

```python
import pickn

# Configuration
sdk = pickn.PicknSDK()
sdk.config(api_key='pk_test_...', environment='test')

# Créer un paiement
payment = sdk.payments.create({
    'amount': 5000,  # en centimes (50.00€)
    'currency': 'EUR',
    'customer_id': 'cus_abc123',
    'description': 'Achat produit'
})

print(payment['status'])  # 'succeeded'
```

## Documentation

Consultez la documentation complète sur [pickn.fr/developers](https://pickn.fr/developers)
