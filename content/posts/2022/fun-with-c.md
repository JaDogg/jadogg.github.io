---
title: "Fun with C and C++ Part 01 - Loops"
summary: "for vs while vs do-while"
date: 2022-02-13
tags:
  - c
  - assembly
---



I'm thinking of writing about what I learn about C and C++. Writing allow me to think slowly and properly understand things.
If you think about it, `for` loop can be done with a `while` loop. Even `do-while` can be simulated with a `while` if you add some duplicate code before.<div class="highlight"><pre><span></span><span class="kt">int</span><span class="w"> </span><span class="nf">main</span><span class="p">(</span><span class="kt">void</span><span class="p">)</span><span class="w"> </span><span class="p">{</span><span class="w"></span>
<span class="w">    </span><span class="kt">int</span><span class="w"> </span><span class="n">i</span><span class="w"> </span><span class="o">=</span><span class="w"> </span><span class="mi">1</span><span class="p">;</span><span class="w"></span>
<span class="w">    </span><span class="kt">int</span><span class="w"> </span><span class="n">j</span><span class="w"> </span><span class="o">=</span><span class="w"> </span><span class="mi">0</span><span class="p">;</span><span class="w"></span>
<span class="w">    </span><span class="k">while</span><span class="w"> </span><span class="p">(</span><span class="n">i</span><span class="w"> </span><span class="o">&lt;=</span><span class="w"> </span><span class="mi">10</span><span class="p">)</span><span class="w"> </span><span class="p">{</span><span class="w"></span>
<span class="w">       </span><span class="n">j</span><span class="w"> </span><span class="o">+=</span><span class="w"> </span><span class="n">i</span><span class="p">;</span><span class="w"></span>
<span class="w">       </span><span class="n">i</span><span class="o">++</span><span class="p">;</span><span class="w"></span>
<span class="w">    </span><span class="p">}</span><span class="w"></span>
<span class="w">    </span><span class="k">return</span><span class="w"> </span><span class="n">j</span><span class="p">;</span><span class="w"></span>
<span class="p">}</span><span class="w"></span>
</pre></div>

---

<div class="highlight"><pre><span></span><span class="nl">main:</span><span class="w"></span>
<span class="w">        </span><span class="c1">; save stack pointer</span>
<span class="w">        </span><span class="nf">push</span><span class="w">    </span><span class="no">rbp</span><span class="w"></span>
<span class="w">        </span><span class="nf">mov</span><span class="w">     </span><span class="no">rbp</span><span class="p">,</span><span class="w"> </span><span class="no">rsp</span><span class="w"></span>
<span class="w">        </span><span class="c1">; int i = 1</span>
<span class="w">        </span><span class="nf">mov</span><span class="w">     </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-4</span><span class="p">],</span><span class="w"> </span><span class="mi">1</span><span class="w"></span>
<span class="w">        </span><span class="c1">; int j = 0</span>
<span class="w">        </span><span class="nf">mov</span><span class="w">     </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-8</span><span class="p">],</span><span class="w"> </span><span class="mi">0</span><span class="w"></span>
<span class="w">        </span><span class="c1">; go to .L2</span>
<span class="w">        </span><span class="nf">jmp</span><span class="w">     </span><span class="no">.L2</span><span class="w"></span>
<span class="nl">.L3:</span><span class="w"></span>
<span class="w">        </span><span class="c1">; eax = i</span>
<span class="w">        </span><span class="nf">mov</span><span class="w">     </span><span class="no">eax</span><span class="p">,</span><span class="w"> </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-4</span><span class="p">]</span><span class="w"></span>
<span class="w">        </span><span class="c1">; j += eax</span>
<span class="w">        </span><span class="nf">add</span><span class="w">     </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-8</span><span class="p">],</span><span class="w"> </span><span class="no">eax</span><span class="w"></span>
<span class="w">        </span><span class="c1">; i += 1</span>
<span class="w">        </span><span class="nf">add</span><span class="w">     </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-4</span><span class="p">],</span><span class="w"> </span><span class="mi">1</span><span class="w"></span>
<span class="nl">.L2:</span><span class="w"></span>
<span class="w">        </span><span class="c1">; compare i and 10</span>
<span class="w">        </span><span class="nf">cmp</span><span class="w">     </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-4</span><span class="p">],</span><span class="w"> </span><span class="mi">10</span><span class="w"></span>
<span class="w">        </span><span class="c1">; if less than or eq jump to .L3</span>
<span class="w">        </span><span class="nf">jle</span><span class="w">     </span><span class="no">.L3</span><span class="w"></span>
<span class="w">        </span><span class="c1">; eax = j</span>
<span class="w">        </span><span class="nf">mov</span><span class="w">     </span><span class="no">eax</span><span class="p">,</span><span class="w"> </span><span class="no">DWORD</span><span class="w"> </span><span class="no">PTR</span><span class="w"> </span><span class="p">[</span><span class="no">rbp-8</span><span class="p">]</span><span class="w"></span>
<span class="w">        </span><span class="c1">; revert stack pointer back to previous value</span>
<span class="w">        </span><span class="nf">pop</span><span class="w">     </span><span class="no">rbp</span><span class="w"></span>
<span class="w">        </span><span class="c1">; return eax</span>
<span class="w">        </span><span class="nf">ret</span><span class="w"></span>
</pre></div>

---

📝<small>
x86-64 gcc 11.2 with `-O0`
</small>

---

