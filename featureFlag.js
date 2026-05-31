// featureFlag.js
require('dotenv').config();

// 💡 유저 ID를 기반으로 항상 똑같은 숫자를 반환하는 해시 함수 (A/B 테스트 일관성 보장)
function getUserHash(userId) {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
        hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash);
}

const Flags = {
    // 1. 환경 변수 기반 플래그 (.env에 NEW_UI_ENABLED=true 로 설정)
    isNewUIEnabled: () => process.env.NEW_UI_ENABLED === 'true',

    // 2. 대상 사용자(Target User) 기반 플래그 (특정 VIP 유저에게만 오픈)
    isBetaFeatureEnabled: (userId) => {
        const targetUsers = ['user_hwa', 'tester_01', 'admin_99'];
        return targetUsers.includes(userId);
    },

    // 3. A/B 테스트 (Variant A / B 할당) - 50:50 분배
    getABTestVariant: (experimentName, userId) => {
        const hash = getUserHash(userId + experimentName); // 유저와 실험명을 조합
        const variant = hash % 2 === 0 ? 'A' : 'B';
        
        // 요구사항: 이벤트 추적 로직 (로깅)
        console.log(`[EVENT TRACKING] Experiment: ${experimentName} | User: ${userId} | Assigned Variant: ${variant}`);
        return variant;
    },

    // 4. (선택과제) 카나리 롤아웃 (0 ~ 100% 제어)
    isCanaryEnabled: (featureName, userId, percentage) => {
        const hash = getUserHash(userId + featureName);
        // 0~99 사이의 난수 생성 (유저 고정)
        const userPercentile = hash % 100; 
        return userPercentile < percentage;
    }
};

module.exports = Flags;