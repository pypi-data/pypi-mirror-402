const {
  SvelteComponent: I,
  append_hydration: m,
  attr: z,
  children: y,
  claim_element: h,
  claim_space: N,
  claim_text: v,
  destroy_each: q,
  detach: _,
  element: d,
  empty: b,
  ensure_array_like: k,
  get_svelte_dataset: D,
  init: O,
  insert_hydration: u,
  noop: A,
  safe_not_equal: S,
  set_data: U,
  space: j,
  text: p,
  toggle_class: o
} = window.__gradio__svelte__internal;
function C(s, e, l) {
  const t = s.slice();
  return t[3] = e[l], t;
}
function E(s) {
  let e, l = Array.isArray(
    /*value*/
    s[0]
  ) && /*value*/
  s[0].length > 3, t, a = k(Array.isArray(
    /*value*/
    s[0]
  ) ? (
    /*value*/
    s[0].slice(0, 3)
  ) : [
    /*value*/
    s[0]
  ]), f = [];
  for (let i = 0; i < a.length; i += 1)
    f[i] = w(C(s, a, i));
  let n = l && L();
  return {
    c() {
      for (let i = 0; i < f.length; i += 1)
        f[i].c();
      e = j(), n && n.c(), t = b();
    },
    l(i) {
      for (let c = 0; c < f.length; c += 1)
        f[c].l(i);
      e = N(i), n && n.l(i), t = b();
    },
    m(i, c) {
      for (let r = 0; r < f.length; r += 1)
        f[r] && f[r].m(i, c);
      u(i, e, c), n && n.m(i, c), u(i, t, c);
    },
    p(i, c) {
      if (c & /*Array, value*/
      1) {
        a = k(Array.isArray(
          /*value*/
          i[0]
        ) ? (
          /*value*/
          i[0].slice(0, 3)
        ) : [
          /*value*/
          i[0]
        ]);
        let r;
        for (r = 0; r < a.length; r += 1) {
          const g = C(i, a, r);
          f[r] ? f[r].p(g, c) : (f[r] = w(g), f[r].c(), f[r].m(e.parentNode, e));
        }
        for (; r < f.length; r += 1)
          f[r].d(1);
        f.length = a.length;
      }
      c & /*value*/
      1 && (l = Array.isArray(
        /*value*/
        i[0]
      ) && /*value*/
      i[0].length > 3), l ? n || (n = L(), n.c(), n.m(t.parentNode, t)) : n && (n.d(1), n = null);
    },
    d(i) {
      i && (_(e), _(t)), q(f, i), n && n.d(i);
    }
  };
}
function w(s) {
  let e, l, t, a = (
    /*path*/
    s[3] + ""
  ), f;
  return {
    c() {
      e = d("li"), l = d("code"), t = p("./"), f = p(a);
    },
    l(n) {
      e = h(n, "LI", {});
      var i = y(e);
      l = h(i, "CODE", {});
      var c = y(l);
      t = v(c, "./"), f = v(c, a), c.forEach(_), i.forEach(_);
    },
    m(n, i) {
      u(n, e, i), m(e, l), m(l, t), m(l, f);
    },
    p(n, i) {
      i & /*value*/
      1 && a !== (a = /*path*/
      n[3] + "") && U(f, a);
    },
    d(n) {
      n && _(e);
    }
  };
}
function L(s) {
  let e, l = "...";
  return {
    c() {
      e = d("li"), e.textContent = l, this.h();
    },
    l(t) {
      e = h(t, "LI", { class: !0, "data-svelte-h": !0 }), D(e) !== "svelte-17d9ayl" && (e.textContent = l), this.h();
    },
    h() {
      z(e, "class", "extra svelte-1u88z5n");
    },
    m(t, a) {
      u(t, e, a);
    },
    d(t) {
      t && _(e);
    }
  };
}
function B(s) {
  let e, l = (
    /*value*/
    s[0] && E(s)
  );
  return {
    c() {
      e = d("ul"), l && l.c(), this.h();
    },
    l(t) {
      e = h(t, "UL", { class: !0 });
      var a = y(e);
      l && l.l(a), a.forEach(_), this.h();
    },
    h() {
      z(e, "class", "svelte-1u88z5n"), o(
        e,
        "table",
        /*type*/
        s[1] === "table"
      ), o(
        e,
        "gallery",
        /*type*/
        s[1] === "gallery"
      ), o(
        e,
        "selected",
        /*selected*/
        s[2]
      );
    },
    m(t, a) {
      u(t, e, a), l && l.m(e, null);
    },
    p(t, [a]) {
      /*value*/
      t[0] ? l ? l.p(t, a) : (l = E(t), l.c(), l.m(e, null)) : l && (l.d(1), l = null), a & /*type*/
      2 && o(
        e,
        "table",
        /*type*/
        t[1] === "table"
      ), a & /*type*/
      2 && o(
        e,
        "gallery",
        /*type*/
        t[1] === "gallery"
      ), a & /*selected*/
      4 && o(
        e,
        "selected",
        /*selected*/
        t[2]
      );
    },
    i: A,
    o: A,
    d(t) {
      t && _(e), l && l.d();
    }
  };
}
function F(s, e, l) {
  let { value: t } = e, { type: a } = e, { selected: f = !1 } = e;
  return s.$$set = (n) => {
    "value" in n && l(0, t = n.value), "type" in n && l(1, a = n.type), "selected" in n && l(2, f = n.selected);
  }, [t, a, f];
}
class G extends I {
  constructor(e) {
    super(), O(this, e, F, B, S, { value: 0, type: 1, selected: 2 });
  }
}
export {
  G as default
};
