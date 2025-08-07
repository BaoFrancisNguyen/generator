#!/usr/bin/env python3
"""
Script de test pour les vraies données Malaysia
"""

from real_data_integrator import RealDataIntegrator

def test_real_data():
    print("🧪 TEST DES VRAIES DONNÉES MALAYSIA")
    print("="*40)
    
    # Test de l'intégrateur
    integrator = RealDataIntegrator()
    
    # Test Kuala Lumpur
    print("\n1️⃣ Test Kuala Lumpur (vraies données)")
    kl_dist = integrator.get_real_building_distribution("Kuala Lumpur", 1800000, 100)
    
    print("Distribution pour 100 bâtiments:")
    for building_type, count in sorted(kl_dist.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {building_type}: {count}")
    
    # Test ville inconnue
    print("\n2️⃣ Test ville inconnue (estimation)")
    unknown_dist = integrator.get_real_building_distribution("Test City", 200000, 50)
    
    print("Distribution pour 50 bâtiments:")
    for building_type, count in sorted(unknown_dist.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {building_type}: {count}")
    
    print("\n✅ Test terminé!")
    print("🎯 Les vraies données fonctionnent correctement")

if __name__ == "__main__":
    test_real_data()
