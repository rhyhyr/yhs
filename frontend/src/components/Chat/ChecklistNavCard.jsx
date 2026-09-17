import { useApp } from '../../hooks/useApp';
import { getMockChecklist } from '../../data/mockChecklistData';

// checklistId → 이동할 화면 ID
const CHECKLIST_SCREEN = {
  'arc-renew':           's-arc-checklist',
  'visa-extension':      's-step',
  'school-registration': 's-school-checklist',
};

/**
 * 체크리스트 생성 후 채팅 영역에 표시되는 이동 버튼 카드
 * 탭하면 해당 체크리스트 화면으로 이동합니다.
 */
export default function ChecklistNavCard({ checklistId }) {
  const { navigate } = useApp();
  const checklist = getMockChecklist(checklistId);
  if (!checklist) return null;

  const screenId = CHECKLIST_SCREEN[checklistId];

  return (
    <div
      className="cl-nav-card"
      style={{ borderColor: checklist.color, background: `${checklist.color}0D` }}
      onClick={() => navigate(screenId)}
    >
      <div className="cl-nav-icon">📋</div>
      <div className="cl-nav-body">
        <div className="cl-nav-title" style={{ color: checklist.color }}>
          체크리스트
        </div>
        <div className="cl-nav-sub">
          {checklist.title} · {checklist.items.length}개 항목
        </div>
      </div>
      <div className="cl-nav-arrow" style={{ color: checklist.color }}>›</div>
    </div>
  );
}
