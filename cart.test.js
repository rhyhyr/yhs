const Cart = require('./cart');

describe('장바구니 TDD 핵심 기능 테스트 (Coverage 100%)', () => {
  let cart = [];

  test('1. addItem: 장바구니에 상품을 추가할 수 있다', () => {
    cart = Cart.addItem(cart, { id: 1, name: '사과', price: 1000 });
    expect(cart.length).toBe(1);
    expect(cart[0].name).toBe('사과');
  });

  test('2. calculateTotal: 총 상품 금액을 계산할 수 있다', () => {
    cart = Cart.addItem(cart, { id: 2, name: '바나나', price: 2000 });
    expect(Cart.calculateTotal(cart)).toBe(3000);
  });

  test('3. applyDiscount: 총액에 할인율을 적용할 수 있다', () => {
    const total = Cart.calculateTotal(cart); // 3000원
    expect(Cart.applyDiscount(total, 10)).toBe(2700); // 10% 할인
  });

  test('4. removeItem: 특정 상품을 뺄 수 있다', () => {
    cart = Cart.removeItem(cart, 1); // 사과(id:1) 삭제
    expect(cart.length).toBe(1);
    expect(cart[0].id).toBe(2);
  });

  test('5. clear: 장바구니를 초기화할 수 있다', () => {
    cart = Cart.clear();
    expect(cart.length).toBe(0);
  });
});