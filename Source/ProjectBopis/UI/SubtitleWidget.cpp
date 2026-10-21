#include "UI/SubtitleWidget.h"
#include "ProjectBopisCharacter.h"

FText USubtitleWidget::GetSubtitleText() const
{
	const AProjectBopisCharacter* Player = GetPlayerCharacter();
	return Player ? Player->GetSubtitle() : FText::GetEmpty();
}

bool USubtitleWidget::HasSubtitle() const
{
	return !GetSubtitleText().IsEmpty();
}
