// Copyright Epic Games, Inc. All Rights Reserved.

#include "UI/GameMessageSubsystem.h"
#include "Weapons/WeaponBase.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"

namespace
{
	/** What picking up ammo says, by type. One place, so every source of a type words it the
	    same and merges into one line. */
	FText AmmoMessagePattern(EAmmoType Type)
	{
		switch (Type)
		{
		case EAmmoType::Pistol45:        return NSLOCTEXT("GameMessages", "Pistol45", "Picked up {Amount} .45 rounds");
		case EAmmoType::Pistol9mm:       return NSLOCTEXT("GameMessages", "Pistol9mm", "Picked up {Amount} 9mm rounds");
		case EAmmoType::HighPowerPistol: return NSLOCTEXT("GameMessages", "HighPowerPistol", "Picked up {Amount} .357 rounds");
		case EAmmoType::MachinePistol:   return NSLOCTEXT("GameMessages", "MachinePistol", "Picked up {Amount} machine pistol rounds");
		case EAmmoType::SubmachineGun:   return NSLOCTEXT("GameMessages", "SubmachineGun", "Picked up {Amount} submachine gun rounds");
		case EAmmoType::Rifle:           return NSLOCTEXT("GameMessages", "Rifle", "Picked up {Amount} 5.56 rounds");
		case EAmmoType::Carbine:         return NSLOCTEXT("GameMessages", "Carbine", "Picked up {Amount} 5.45 rounds");
		case EAmmoType::Sniper:          return NSLOCTEXT("GameMessages", "Sniper", "Picked up {Amount} sniper rounds");
		case EAmmoType::AutoShotgun:
		case EAmmoType::PumpShotgun:     return NSLOCTEXT("GameMessages", "Shotgun", "Picked up {Amount} shotgun shells");
		case EAmmoType::Grenade:         return NSLOCTEXT("GameMessages", "Grenade", "Picked up {Amount} {Amount}|plural(one=grenade,other=grenades)");
		case EAmmoType::LauncherGrenade: return NSLOCTEXT("GameMessages", "LauncherGrenade", "Picked up {Amount} launcher {Amount}|plural(one=grenade,other=grenades)");
		case EAmmoType::FirstAid:        return NSLOCTEXT("GameMessages", "FirstAid", "Picked up {Amount} first aid {Amount}|plural(one=kit,other=kits)");
		}
		return NSLOCTEXT("GameMessages", "Ammo", "Picked up {Amount} rounds");
	}
}

UGameMessageSubsystem* UGameMessageSubsystem::GetFeed(const UObject* WorldContextObject)
{
	const UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
	const ULocalPlayer* Player = World ? World->GetFirstLocalPlayerFromController() : nullptr;
	return Player ? Player->GetSubsystem<UGameMessageSubsystem>() : nullptr;
}

void UGameMessageSubsystem::ShowGameMessage(const UObject* WorldContextObject, const FText& Message, float Seconds)
{
	if (UGameMessageSubsystem* Feed = GetFeed(WorldContextObject))
	{
		Feed->AddMessage(Message, Seconds);
	}
}

void UGameMessageSubsystem::ShowCountedGameMessage(const UObject* WorldContextObject, const FText& Pattern, int32 Amount, float Seconds)
{
	if (UGameMessageSubsystem* Feed = GetFeed(WorldContextObject))
	{
		Feed->AddCountedMessage(Pattern, Amount, Seconds);
	}
}

void UGameMessageSubsystem::ShowAmmoMessage(const UObject* WorldContextObject, EAmmoType Type, int32 Amount)
{
	ShowCountedGameMessage(WorldContextObject, AmmoMessagePattern(Type), Amount);
}

void UGameMessageSubsystem::AddMessage(const FText& Message, float Seconds)
{
	AddLine(Message.ToString(), Message, 0, Seconds);
}

void UGameMessageSubsystem::AddCountedMessage(const FText& Pattern, int32 Amount, float Seconds)
{
	// The same pattern still up: this adds to its total.
	const FString Key = Pattern.ToString();
	const double Now = FPlatformTime::Seconds();
	for (const FGameMessage& Line : Messages)
	{
		if (Line.Key == Key && Line.EndTime > Now)
		{
			Amount += Line.Amount;
			break;
		}
	}
	AddLine(Key, FText::FormatNamed(Pattern, TEXT("Amount"), Amount), Amount, Seconds);
}

void UGameMessageSubsystem::AddLine(const FString& Key, const FText& Text, int32 Amount, float Seconds)
{
	if (Text.IsEmpty() || Seconds <= 0.0f)
	{
		return;
	}

	// Out go the expired lines and the one this replaces; a full feed then drops its oldest.
	const double Now = FPlatformTime::Seconds();
	Messages.RemoveAll([Now, &Key](const FGameMessage& Line) { return Line.EndTime <= Now || Line.Key == Key; });
	if (Messages.Num() >= MaxMessages)
	{
		Messages.RemoveAt(0);
	}
	Messages.Add({ Key, Text, Amount, Now + Seconds });
}
