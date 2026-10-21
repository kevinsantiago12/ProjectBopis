#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "EncounterEvent.generated.h"

class AEnemyBase;
class AEncounterTrigger;
class AEncounterEvent;
class USoundBase;
class UAnimMontage;
class UAudioComponent;
class UTextRenderComponent;
class UBillboardComponent;

UENUM(BlueprintType)
enum class EEncounterStepType : uint8
{
	/** A speaker says a line: their voice from their head, and a subtitle if the player's near. */
	SayLine,
	/** A pause. */
	Wait,
	/** A speaker acts something out without a line: a shrug, a nod, lighting a cigarette. */
	PlayAnim,
	/** A speaker walks (or runs) to a point; the next step can wait for them to get there. */
	MoveTo,
	/** A speaker turns to face someone or something (body and head), and keeps facing it. */
	FaceTo,
	/** Sets off an encounter trigger, as if the player had walked into it: the fight starts on a
	    story beat. Its enemies being alerted ends this event as finished, not interrupted. */
	SetOffEncounter,
	/** Starts another event (alongside this one). */
	StartEvent
};

/** One step of a scripted event. */
USTRUCT(BlueprintType)
struct FEncounterEventStep
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, Category = "Step")
	EEncounterStepType Type = EEncounterStepType::SayLine;

	/** Who does it: an enemy placed in the level. If they're dead by then, the step is skipped. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim || Type == EEncounterStepType::MoveTo || Type == EEncounterStepType::FaceTo", EditConditionHides))
	TObjectPtr<AEnemyBase> Speaker;

	/** Or, with Speaker empty, a spawned one: the living enemy with this tag (a trigger spawn's
	    Tag), looked up when the step comes. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim || Type == EEncounterStepType::MoveTo || Type == EEncounterStepType::FaceTo", EditConditionHides))
	FName SpeakerTag;

	/** Shown before the line in the subtitle ("Name: line"). Empty: the line alone. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SayLine", EditConditionHides))
	FText SpeakerName;

	/** The voice. None: a subtitle-only line, timed by its length. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SayLine", EditConditionHides))
	TObjectPtr<USoundBase> Sound;

	UPROPERTY(EditAnywhere, Category = "Step", meta = (MultiLine = "true", EditCondition = "Type == EEncounterStepType::SayLine", EditConditionHides))
	FText Subtitle;

	/** Played on the speaker (a montage on DefaultSlot). With a line: loops until the line ends.
	    Play Anim: loops for its Duration if one is set, else plays once. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim", EditConditionHides))
	TObjectPtr<UAnimMontage> Animation;

	/** Play Anim: the next step waits for it. Off: the next step starts at once (a gesture while
	    someone else talks). */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::PlayAnim", EditConditionHides))
	bool bWaitForAnim = true;

	/** Move To: where to go (any actor: a patrol or ambush point). Face To: who or what to face.
	    Face To with nothing set (here or in TargetTag): stops facing. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::MoveTo || Type == EEncounterStepType::FaceTo", EditConditionHides))
	TObjectPtr<AActor> Target;

	/** Face To, with Target empty: the living enemy with this tag (the other speaker). */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::FaceTo", EditConditionHides))
	FName TargetTag;

	/** Move To: runs instead of walking. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::MoveTo", EditConditionHides))
	bool bRun = false;

	/** Move To: how close (cm) to the Target counts as there. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (ClampMin = "0.0", EditCondition = "Type == EEncounterStepType::MoveTo", EditConditionHides))
	float AcceptanceRadius = 50.0f;

	/** Move To: the next step waits until they arrive. Off: the next step starts at once (he walks
	    off while the other one keeps talking). */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::MoveTo", EditConditionHides))
	bool bWaitForArrival = true;

	/** Set Off Encounter: the trigger to fire. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::SetOffEncounter", EditConditionHides))
	TObjectPtr<AEncounterTrigger> Encounter;

	/** Start Event: the event to start. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (EditCondition = "Type == EEncounterStepType::StartEvent", EditConditionHides))
	TObjectPtr<AEncounterEvent> Event;

	/** Seconds. A wait: how long. A line: 0 = the sound's length (or a reading time from the
	    subtitle without one). An anim: 0 = its length. Above 0 overrides it. */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (ClampMin = "0.0", EditCondition = "Type == EEncounterStepType::Wait || Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim", EditConditionHides))
	float Duration = 0.0f;

	/** A beat after a line, an anim, or arriving, before the next step (seconds). */
	UPROPERTY(EditAnywhere, Category = "Step", meta = (ClampMin = "0.0", EditCondition = "Type == EEncounterStepType::SayLine || Type == EEncounterStepType::PlayAnim || Type == EEncounterStepType::MoveTo", EditConditionHides))
	float PauseAfter = 0.3f;
};

/**
 *  A scripted moment: an ordered list of steps (lines, anims, moves, facing, waits, setting off a
 *  fight, starting other events) run once, started by an encounter trigger, the level, or another
 *  event. The overheard conversation: enemies talk among themselves as the player comes near. If
 *  any speaker is alerted or killed, it stops dead — the line cuts off and the one who noticed
 *  shouts the reaction line (or his Spotted bark). What runs next can branch: EventsOnFinished
 *  if it played out, EventsOnInterrupted if the player broke it up.
 */
UCLASS()
class PROJECTBOPIS_API AEncounterEvent : public AActor
{
	GENERATED_BODY()

public:
	AEncounterEvent();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void Tick(float DeltaSeconds) override;
	virtual bool ShouldTickIfViewportsOnly() const override { return true; }

	/** Runs the steps from the top (once; later calls do nothing). */
	UFUNCTION(BlueprintCallable, Category = "Encounter")
	void StartEvent();

	bool IsRunning() const { return bRunning; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<USceneComponent> Root;

	/** Editor-only text: name and step count. */
	UPROPERTY(VisibleAnywhere, Category = "Encounter")
	TObjectPtr<UTextRenderComponent> Label;

#if WITH_EDITORONLY_DATA
	/** Editor-only icon, to click on. */
	UPROPERTY()
	TObjectPtr<UBillboardComponent> Icon;
#endif

	UPROPERTY(EditInstanceOnly, Category = "Encounter")
	TArray<FEncounterEventStep> Steps;

	/** Starts by itself when the level does. Otherwise a trigger starts it (its EventsToStart),
	    or another event (a Start Event step, or its chains). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bStartOnBeginPlay = false;

	/** Subtitles show only while the player is within this of the speaker (cm). 0: always. */
	UPROPERTY(EditAnywhere, Category = "Encounter|Voice", meta = (ClampMin = "0.0"))
	float SubtitleRange = 3000.0f;

	/** Voices are full volume within this of the speaker (cm)... */
	UPROPERTY(EditAnywhere, Category = "Encounter|Voice", meta = (ClampMin = "0.0"))
	float VoiceFullRange = 400.0f;

	/** ...and fade out over this much further (cm). */
	UPROPERTY(EditAnywhere, Category = "Encounter|Voice", meta = (ClampMin = "0.0"))
	float VoiceFalloff = 2500.0f;

	/** Cut short by a speaker being alerted: the one who noticed says this. None (and no
	    subtitle): he gives his Spotted bark instead. */
	UPROPERTY(EditAnywhere, Category = "Encounter|Interrupt")
	TObjectPtr<USoundBase> InterruptSound;

	UPROPERTY(EditAnywhere, Category = "Encounter|Interrupt", meta = (MultiLine = "true"))
	FText InterruptSubtitle;

	/** Started when it plays out: runs to the end, or ends by setting off its encounter. */
	UPROPERTY(EditInstanceOnly, Category = "Encounter|Chain")
	TArray<TObjectPtr<AEncounterEvent>> EventsOnFinished;

	/** Started when the player breaks it up (a speaker alerted or killed). */
	UPROPERTY(EditInstanceOnly, Category = "Encounter|Chain")
	TArray<TObjectPtr<AEncounterEvent>> EventsOnInterrupted;

	/** Editor only: lines to its speakers (purple), where they move or look (green), the
	    trigger it sets off (orange) and the events it starts (white). */
	UPROPERTY(EditAnywhere, Category = "Encounter")
	bool bDrawLinks = true;

private:
	void RunNextStep();
	void Interrupt(AEnemyBase* Noticed);

	/** Played out: tidies up and starts EventsOnFinished. */
	void Finish();

	/** Ends it either way: stops its anims and hands its speakers back to their own business. */
	void EndRun();

	void Say(AEnemyBase* Speaker, USoundBase* Sound, const FText& SpeakerName, const FText& Line, float Seconds);
	void DrawLinks() const;

	/** Blends out the current line's animation, if it's still playing. */
	void StopLineAnim();

	/** Plays a step's montage on the speaker; looped, it repeats until the step ends. Returns its
	    length (0 if it didn't play). */
	float PlayStepAnim(AEnemyBase* Speaker, UAnimMontage* Anim, bool bLoop);

	/** A step's speaker: the placed one, else the living enemy tagged SpeakerTag. */
	AEnemyBase* FindSpeaker(const FEncounterEventStep& Step) const;

	/** The living enemy with this tag. */
	AEnemyBase* FindTagged(FName Tag) const;

	/** Steps a speaker takes part in (lines, anims, moves, facing). */
	static bool HasSpeaker(EEncounterStepType Type);

	/** Everyone who takes part: any of them alerted or dead stops it. */
	TArray<TWeakObjectPtr<AEnemyBase>> Speakers;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> CurrentVoice;

	/** Who is acting out the current step, and with what: stopped when the step ends. */
	TWeakObjectPtr<AEnemyBase> LineSpeaker;

	UPROPERTY(Transient)
	TObjectPtr<UAnimMontage> LineAnim;

	/** A Move To being waited on: the next step comes when he arrives (then its PauseAfter). */
	TWeakObjectPtr<AEnemyBase> MovingSpeaker;
	float MovePauseAfter = 0.0f;

	int32 StepIndex = -1;
	float StepTimeLeft = 0.0f;
	bool bRunning = false;
	bool bDone = false;

	/** It has set off its encounter: speakers being alerted now is the plan, not the player
	    catching them out. */
	bool bSetOff = false;
};
