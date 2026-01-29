PepKit Documentation
====================

.. raw:: html

  <div class="hero" role="banner" aria-label="PepKit hero">
    <div class="hero-left">
      <p class="hero-title">PepKit</p>
      <p class="hero-subtitle">
        A modular toolkit for peptide chemistry, graph-based modeling, PDB queries,
        and structure rescoring.
      </p>

      <div class="badges" role="navigation" aria-label="PepKit modules">
        <a class="badge badge-link" href="chem.html" title="Chem — FASTA ⇄ SMILES, descriptors & properties" aria-label="Chem: FASTA to SMILES and descriptors">
          <!-- chemistry flask icon (small) -->
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
            <path d="M10 2v4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M6 6h12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M16 10l-4 6-4-6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>FASTA ⇄ SMILES, descriptors &amp; properties</span>
        </a>

        <a class="badge badge-link" href="graph.html" title="Graph — Graph-based peptide models" aria-label="Graph: graph-based peptide models">
          <!-- graph icon -->
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
            <circle cx="6" cy="17" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
            <circle cx="12" cy="7" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
            <circle cx="18" cy="17" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
            <path d="M7.2 15.8L11 8.4M13 8.4L16.8 15.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Graph-based peptide models</span>
        </a>

        <a class="badge badge-link" href="query.html" title="Query — PDB queries" aria-label="Query: PDB queries">
          <!-- magnifier icon -->
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
            <circle cx="11" cy="11" r="5" stroke="currentColor" stroke-width="1.6"></circle>
            <path d="M21 21l-4.3-4.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"></path>
          </svg>
          <span>PDB query</span>
        </a>

        <a class="badge badge-link" href="modelling.html" title="Modeling — Post-processing & rescoring" aria-label="Modeling: post-processing and rescoring">
          <!-- settings / rescore icon -->
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false">
            <path d="M4 6h16" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M7 12h10" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            <path d="M10 18h4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
          </svg>
          <span>Post-processing &amp; rescoring</span>
        </a>
      </div>
    </div>
  </div>


.. raw:: html

   <p style="text-align:center">
     <a href="getting_started.html" title="Open Getting Started — PepKit">
       <img src="_static/pepkit_package.png"
            alt="High-level PepKit module overview (chemistry, graphs, queries, modeling)"
            class="clickable-figure-img"
            style="max-width:85%; height:auto; border-radius:8px; box-shadow: 0 6px 20px rgba(0,0,0,0.06);" />
     </a>
   </p>


At a glance
-----------

.. raw:: html

   <div class="at-a-glance" role="region" aria-label="At a glance">
     <div class="info-card" role="article" aria-labelledby="ia1-title">
       <div class="info-icon" aria-hidden="true">
         <!-- lightning / features icon -->
         <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
           <path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="info-body">
         <h4 id="ia1-title">What it helps with</h4>
         <p>Peptide format conversion, dataset standardization, feature extraction, graph-based modeling, PDB queries, and structure-level post-processing and rescoring.</p>
       </div>
     </div>

     <div class="info-card" role="article" aria-labelledby="ia2-title">
       <div class="info-icon" aria-hidden="true">
         <!-- users icon -->
         <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
           <path d="M16 11c1.657 0 3-1.567 3-3.5S17.657 4 16 4s-3 1.567-3 3.5S14.343 11 16 11zM8 11c1.657 0 3-1.567 3-3.5S9.657 4 8 4 5 5.567 5 7.5 6.343 11 8 11z" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M2 20c0-2.8 4-5 8-5s8 2.2 8 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="info-body">
         <h4 id="ia2-title">Who it is for</h4>
         <p>Users building peptide datasets, exploring graph-based peptide representations, querying peptide–protein complexes, or benchmarking structural models.</p>
       </div>
     </div>

     <div class="info-card install-card" role="article" aria-labelledby="ia3-title">
       <div class="info-icon" aria-hidden="true">
         <!-- install / box icon -->
         <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
           <path d="M21 16V8a2 2 0 0 0-1-1.732L13 3l-7 3.268A2 2 0 0 0 5 8v8a2 2 0 0 0 1 1.732L11 21l7-3.268A2 2 0 0 0 19 16z" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M3 7l9 5 9-5" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="info-body">
         <h4 id="ia3-title">Quick install</h4>
         <p class="install-line"><code>pip install pepkit</code></p>
         <p class="small">Minimal example and full quickstart are in the Getting Started guide.</p>
       </div>
     </div>
   </div>


Start here
----------

.. raw:: html

   <div class="cards" role="list" aria-label="PepKit quick links">
     <a class="card card-link" href="getting_started" role="listitem" aria-label="Getting Started — Install and quick example">
       <div class="card-icon" aria-hidden="true">
         <!-- simple book icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <path d="M3 6.5A2.5 2.5 0 0 1 5.5 4H19" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M19 20.5H5.5A2.5 2.5 0 0 1 3 18V6.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="card-body">
         <h3>Getting Started</h3>
         <p>Install PepKit and run a minimal end-to-end example.</p>
         <ul class="card-tags">
           <li>Quickstart</li><li>Example</li>
         </ul>
         <span class="card-cta">Open guide →</span>
       </div>
     </a>

     <a class="card card-link" href="chem" role="listitem" aria-label="Chem — Sequence and SMILES utilities">
       <div class="card-icon" aria-hidden="true">
         <!-- flask/chem icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <path d="M10 2v4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M6 6h12" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M16 10l-4 6-4-6" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M8 20h8" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="card-body">
         <h3>Chem</h3>
         <p>FASTA ⇄ SMILES conversion, standardization, and descriptors.</p>
         <ul class="card-tags">
           <li>FASTA</li><li>SMILES</li><li>RDKit</li>
         </ul>
         <span class="card-cta">Explore chem →</span>
       </div>
     </a>

     <a class="card card-link" href="graph" role="listitem" aria-label="Graph — Graph-based peptide modelling">
       <div class="card-icon" aria-hidden="true">
         <!-- graph icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <circle cx="6" cy="17" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
           <circle cx="12" cy="7" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
           <circle cx="18" cy="17" r="1.6" stroke="currentColor" stroke-width="1.2" fill="none"></circle>
           <path d="M7.2 15.8L11 8.4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
           <path d="M13 8.4L16.8 15.8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
         </svg>
       </div>
       <div class="card-body">
         <h3>Graph</h3>
         <p>Peptide modeling using graph-based representations and utilities.</p>
         <ul class="card-tags">
           <li>Graph</li><li>Alignment</li>
         </ul>
         <span class="card-cta">Explore graph →</span>
       </div>
     </a>

     <a class="card card-link" href="query" role="listitem" aria-label="Query — PDB constraint queries">
       <div class="card-icon" aria-hidden="true">
         <!-- search/magnifier icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <circle cx="11" cy="11" r="5" stroke="currentColor" stroke-width="1.4"></circle>
           <path d="M21 21l-4.3-4.3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"></path>
         </svg>
       </div>
       <div class="card-body">
         <h3>Query</h3>
         <p>Constraint-based PDB queries for peptide–protein complexes.</p>
         <ul class="card-tags">
           <li>PDB</li><li>Filters</li>
         </ul>
         <span class="card-cta">Explore queries →</span>
       </div>
     </a>

     <a class="card card-link" href="modeling" role="listitem" aria-label="Modeling — Postprocess and rescore predicted complexes">
       <div class="card-icon" aria-hidden="true">
         <!-- model/rescore icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <path d="M4 6h16" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
           <path d="M7 12h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
           <path d="M10 18h4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
         </svg>
       </div>
       <div class="card-body">
         <h3>Modeling</h3>
         <p>Post-process and rescore predicted complexes (e.g. AlphaFold outputs).</p>
         <ul class="card-tags">
           <li>Rescore</li><li>AlphaFold</li>
         </ul>
         <span class="card-cta">Explore modeling →</span>
       </div>
     </a>

     <a class="card card-link" href="api" role="listitem" aria-label="API Reference — programmatic interface">
       <div class="card-icon" aria-hidden="true">
         <!-- api/book icon -->
         <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" focusable="false" aria-hidden="true">
           <rect x="4" y="4" width="16" height="16" rx="2" stroke="currentColor" stroke-width="1.2" fill="none"></rect>
           <path d="M8 8h8" stroke="currentColor" stroke-width="1.2"></path>
           <path d="M8 12h8" stroke="currentColor" stroke-width="1.2"></path>
         </svg>
       </div>
       <div class="card-body">
         <h3>API Reference</h3>
         <p>Programmatic reference for PepKit modules and functions.</p>
         <ul class="card-tags">
           <li>API</li><li>Reference</li>
         </ul>
         <span class="card-cta">Explore API →</span>
       </div>
     </a>
   </div>


.. toctree::
   :caption: Contents
   :maxdepth: 2

   Getting Started <getting_started>
   Chemical Modeling <chem>
   Query <query>
   Graph <graph>
   Modeling <modelling>
   API Reference <api>
   Changelog <changelog>
