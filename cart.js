// TDD를 위한 5가지 핵심 비즈니스 로직 (장바구니 기능)
const Cart = {
  // 기능 1: 상품 추가
  addItem: (cart, item) => [...cart, item],
  // 기능 2: 상품 삭제
  removeItem: (cart, itemId) => cart.filter(item => item.id !== itemId),
  // 기능 3: 총액 계산
  calculateTotal: (cart) => cart.reduce((sum, item) => sum + item.price, 0),
  // 기능 4: 할인 적용
  applyDiscount: (total, rate) => total - (total * (rate / 100)),
  // 기능 5: 장바구니 초기화
  clear: () => []
};

module.exports = Cart;