// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WeaponBase.generated.h"

UENUM(BlueprintType)
enum class EWeaponFireMode : uint8
{
	Semi,
	Auto
};

UCLASS()
class PROJECTBOPIS_API AWeaponBase : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AWeaponBase();

	/** Returns the weapon's mesh component **/
	UStaticMeshComponent* GetWeaponMesh() const { return WeaponMesh; };


	UFUNCTION(BlueprintCallable, Category = "Weapon")
	void Fire(const FVector& TraceStart, const FVector& TraceDirection);

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Weapon")
	TObjectPtr<UStaticMeshComponent> WeaponMesh;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	EWeaponFireMode FireMode = EWeaponFireMode::Semi;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float BaseDamage = 10.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	float MaxRange = 5000.0f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Weapon")
	bool bHasZoom = false;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

};
