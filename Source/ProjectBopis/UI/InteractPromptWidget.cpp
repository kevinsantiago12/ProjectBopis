#include "UI/InteractPromptWidget.h"
#include "ProjectBopisCharacter.h"
#include "Gameplay/InteractComponent.h"

FText UInteractPromptWidget::GetPromptText() const
{
	const AProjectBopisCharacter* Player = GetPlayerCharacter();
	const UInteractComponent* Interaction = Player ? Player->GetInteraction() : nullptr;
	return Interaction ? Interaction->GetPromptText() : FText::GetEmpty();
}

bool UInteractPromptWidget::HasPrompt() const
{
	return !GetPromptText().IsEmpty();
}

ESlateVisibility UInteractPromptWidget::GetPromptVisibility() const
{
	return HasPrompt() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed;
}
