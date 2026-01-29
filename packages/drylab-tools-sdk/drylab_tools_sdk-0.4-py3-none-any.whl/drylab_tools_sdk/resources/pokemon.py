"""
Pokemon protein structure prediction tools.

Provides methods to search for tools and execute protein structure prediction jobs.
"""

import os
from typing import Optional, List, Dict, Any

import requests

from drylab_tools_sdk.resources.base import BaseResource
from drylab_tools_sdk.models.pokemon import (
    PokemonTool,
    ToolSearchResult,
    PokemonJobResult,
)


class PokemonResource(BaseResource):
    """
    Pokemon protein structure prediction tools.

    Provides methods to search for tools and execute jobs for:
    - ProteinX: Structure prediction
    - Chai1: Diffusion-based prediction
    - ProteinMPNN: Sequence design
    - Boltz2: Advanced structure prediction

    Example:
        # Search for tools
        result = client.pokemon.search("predict protein structure")
        print(result)

        # Run a job
        job = client.pokemon.chai1(
            output_vault_path="/MyProject/results",
            proteins=[{"sequence": "MVLSPADKTNVK..."}]
        )
        print(job)
    """

    def search(self, query: str) -> ToolSearchResult:
        """
        Search for Pokemon tools using AI-powered semantic matching.

        Args:
            query: Natural language description of what you want to do

        Returns:
            ToolSearchResult with matching tools

        Example:
            result = client.pokemon.search("predict protein structure from sequence")
            print(result)
        """
        try:
            response = self._http.post(
                "/api/v1/ai/pokemon/tools/search",
                json={"query": query}
            )

            tools = [
                PokemonTool(
                    id=t["tool_id"],
                    name=t["name"],
                    description=t["description"],
                    compute_credit=t["compute_credit"],
                )
                for t in response.get("tools", [])
            ]

            return ToolSearchResult(
                tools=tools,
                query=query,
                success=response.get("success", True),
                status=response.get("status", "Search completed."),
            )

        except requests.exceptions.ConnectionError:
            return ToolSearchResult(
                tools=[],
                query=query,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            return ToolSearchResult(
                tools=[],
                query=query,
                success=False,
                status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
            )
        except Exception as e:
            return ToolSearchResult(
                tools=[],
                query=query,
                success=False,
                status=f"Unexpected error while searching tools: {str(e)}. Please report this to the Drylab team.",
            )

    def _read_file_content(self, file_path: str) -> Dict[str, str]:
        """
        Read a local file and return file_name and file_content.

        Args:
            file_path: Path to local file

        Returns:
            Dict with "file_name" and "file_content"
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return {
            "file_name": os.path.basename(file_path),
            "file_content": content,
        }

    def _execute_tool(
        self,
        tool_id: str,
        output_vault_path: str,
        params: Dict[str, Any],
        job_name: Optional[str] = None,
    ) -> PokemonJobResult:
        """
        Internal helper to execute a Pokemon tool job.

        Args:
            tool_id: Tool identifier
            output_vault_path: Vault path for results
            params: Tool-specific parameters
            job_name: Optional job name

        Returns:
            PokemonJobResult
        """
        try:
            # Pokemon jobs can take up to 5 minutes, so use 360s timeout (6 minutes with buffer)
            # This matches the backend timeout setting
            # Use generic /run/{tool_id} endpoint - backend is tool-agnostic
            response = self._http.post(
                f"/api/v1/ai/pokemon/run/{tool_id}",
                json={
                    "output_vault_path": output_vault_path,
                    "job_name": job_name,
                    "params": params,  # params passed through to RunPod as-is
                },
                timeout=360,  # 6 minutes to match backend timeout
                # Note: Retries are handled by the HTTP client but only for 502/503/504 status codes
                # Timeouts won't retry, which is correct for long-running jobs
            )

            return PokemonJobResult(
                tool_id=response.get("tool_id", tool_id),
                vault_path=response.get("vault_path", output_vault_path),
                output_files=response.get("output_files", []),
                execution_time_ms=response.get("execution_time_ms"),
                success=response.get("success", True),
                status=response.get("status", "Job completed successfully."),
            )

        except requests.exceptions.ConnectionError:
            return PokemonJobResult(
                tool_id=tool_id,
                vault_path=output_vault_path,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    return PokemonJobResult(
                        tool_id=tool_id,
                        vault_path=output_vault_path,
                        success=False,
                        status=error_detail,
                    )
                except:
                    return PokemonJobResult(
                        tool_id=tool_id,
                        vault_path=output_vault_path,
                        success=False,
                        status=f"Validation error (HTTP 400). Please check your parameters.",
                    )
            else:
                return PokemonJobResult(
                    tool_id=tool_id,
                    vault_path=output_vault_path,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            # Format error message without including verbose input data
            error_str = str(e)
            # Truncate if it contains 'input' field with large data
            if "'input':" in error_str and len(error_str) > 500:
                # Extract just the error type and message, not the input
                error_str = error_str.split("'input':")[0].rstrip(", ").rstrip()
                if error_str.endswith("["):
                    error_str = error_str[:-1].rstrip()
            return PokemonJobResult(
                tool_id=tool_id,
                vault_path=output_vault_path,
                success=False,
                status=f"Unexpected error: {error_str}. Please report this to the Drylab team.",
            )

    # ============================================================================
    # ProteinX
    # ============================================================================

    def proteinx(
        self,
        output_vault_path: str,
        *,
        # Input mode
        input_mode: str,  # "file" or "manual"
        pdb_file: Optional[str] = None,  # Local path
        cif_file: Optional[str] = None,  # Local path
        # Manual input
        proteins: Optional[List[Dict[str, str]]] = None,
        rnas: Optional[List[Dict[str, str]]] = None,
        dnas: Optional[List[Dict[str, str]]] = None,
        ligands: Optional[List[Dict[str, Any]]] = None,
        ions: Optional[List[Dict[str, str]]] = None,
        modifications: Optional[List[Dict[str, Any]]] = None,
        # Parameters
        model_name: str = "protenix_base_default_v0.5.0",
        seed: int = 20,
        cycle: int = 3,
        sample: int = 5,
        step: int = 200,
        # Constraints
        bonds: Optional[List[Dict[str, Any]]] = None,
        pocket_restraints: Optional[List[Dict[str, Any]]] = None,
        contact_restraints: Optional[List[Dict[str, Any]]] = None,
        job_name: Optional[str] = None,
    ) -> PokemonJobResult:
        """
        Run a ProteinX structure prediction job.

        Args:
            output_vault_path: Vault path where results will be stored
            input_mode: "file" for PDB/CIF upload, "manual" for sequence input
            pdb_file: Local path to PDB file (if input_mode="file")
            cif_file: Local path to CIF file (if input_mode="file")
            proteins: List of protein sequences (if input_mode="manual")
            rnas: List of RNA sequences
            dnas: List of DNA sequences
            ligands: List of ligand molecules
            ions: List of ions
            modifications: List of post-translational modifications
            model_name: Model to use
            seed: Random seed
            cycle: Number of refinement cycles
            sample: Number of structure samples
            step: Number of diffusion steps
            bonds: List of bond constraints
            pocket_restraints: List of pocket restraint constraints
            contact_restraints: List of contact restraint constraints
            job_name: Optional job name

        Returns:
            PokemonJobResult

        Example:
            job = client.pokemon.proteinx(
                output_vault_path="/MyProject/results",
                input_mode="manual",
                proteins=[{"sequence": "MVLSPADKTNVK..."}],
                seed=42
            )
            print(job)
        """
        params: Dict[str, Any] = {
            "job_type": "proteinx",
            "input_mode": input_mode,
            "model_name": model_name,
            "seed": seed,
            "cycle": cycle,
            "sample": sample,
            "step": step,
        }

        # Handle file input
        if input_mode == "file":
            if pdb_file:
                params["pdb_file"] = self._read_file_content(pdb_file)
            if cif_file:
                params["cif_file"] = self._read_file_content(cif_file)
        elif input_mode == "manual":
            if proteins:
                params["proteins"] = proteins
            if rnas:
                params["rnas"] = rnas
            if dnas:
                params["dnas"] = dnas

        if ligands:
            params["ligands"] = ligands
        if ions:
            params["ions"] = ions
        if modifications:
            params["modifications"] = modifications
        if bonds:
            params["bonds"] = bonds
        if pocket_restraints:
            params["pocketRestraints"] = pocket_restraints
        if contact_restraints:
            params["contactRestraints"] = contact_restraints

        return self._execute_tool("proteinx", output_vault_path, params, job_name)

    # ============================================================================
    # Chai1
    # ============================================================================

    def chai1(
        self,
        output_vault_path: str,
        *,
        proteins: Optional[List[Dict[str, str]]] = None,
        rnas: Optional[List[Dict[str, str]]] = None,
        dnas: Optional[List[Dict[str, str]]] = None,
        ligands: Optional[List[Dict[str, str]]] = None,
        glycans: Optional[List[Dict[str, str]]] = None,
        modifications: Optional[List[Dict[str, Any]]] = None,
        num_trunk_samples: int = 1,
        num_recycles: int = 3,
        num_diffn_samples: int = 5,
        num_diffn_timesteps: int = 200,
        seed: int = 20,
        bonds: Optional[List[Dict[str, Any]]] = None,
        pocket_restraints: Optional[List[Dict[str, Any]]] = None,
        contact_restraints: Optional[List[Dict[str, Any]]] = None,
        job_name: Optional[str] = None,
    ) -> PokemonJobResult:
        """
        Run a Chai1 diffusion-based structure prediction job.

        Args:
            output_vault_path: Vault path where results will be stored
            proteins: List of protein sequences
            rnas: List of RNA sequences
            dnas: List of DNA sequences
            ligands: List of ligand SMILES strings
            glycans: List of glycan sequences
            modifications: List of modifications
            num_trunk_samples: Number of trunk samples
            num_recycles: Number of recycles
            num_diffn_samples: Number of diffusion samples
            num_diffn_timesteps: Number of diffusion timesteps
            seed: Random seed
            bonds: List of bond constraints
            pocket_restraints: List of pocket restraint constraints
            contact_restraints: List of contact restraint constraints
            job_name: Optional job name

        Returns:
            PokemonJobResult

        Example:
            job = client.pokemon.chai1(
                output_vault_path="/MyProject/results",
                proteins=[{"sequence": "MVLSPADKTNVK..."}],
                seed=42
            )
            print(job)
        """
        params: Dict[str, Any] = {
            "job_type": "chai1",
            "numTrunkSamples": num_trunk_samples,
            "numRecycles": num_recycles,
            "numDiffnSamples": num_diffn_samples,
            "numDiffnTimesteps": num_diffn_timesteps,
            "seed": seed,
        }

        if proteins:
            params["proteins"] = proteins
        if rnas:
            params["rnas"] = rnas
        if dnas:
            params["dnas"] = dnas
        if ligands:
            params["ligands"] = ligands
        if glycans:
            params["glycans"] = glycans
        if modifications:
            params["modifications"] = modifications
        if bonds:
            params["bonds"] = bonds
        if pocket_restraints:
            params["pocketRestraints"] = pocket_restraints
        if contact_restraints:
            params["contactRestraints"] = contact_restraints

        return self._execute_tool("chai1", output_vault_path, params, job_name)

    # ============================================================================
    # ProteinMPNN
    # ============================================================================

    def proteinmpnn(
        self,
        output_vault_path: str,
        *,
        pdb_data: str = "",
        designedResidues: Dict[str, str] = None,
        numSequences: int = 2,
        temperature: float = 0.1,
        noiseLevel: float = 0.2,
        omitAAs: str = "C",
        bias_AA: str = "W:3.0,P:3.0,C:3.0,A:-3.0",
        bias_AA_per_residue: str = "{}",
        omit_AA_per_residue: str = "{}",
        job_name: Optional[str] = None,
    ) -> PokemonJobResult:
        """
        Run a ProteinMPNN sequence design job.
        
        Signature matches drylab-pokemon/job_request/proteinmpnn.py exactly, with only output_vault_path added.

        Args:
            output_vault_path: Vault path where results will be stored
            pdb_data: PDB file content as string
            designedResidues: Dict mapping chain IDs to residue positions (e.g., {"B": "26 27 28"})
            numSequences: Number of sequences to generate
            temperature: Sampling temperature
            noiseLevel: Noise level
            omitAAs: Amino acids to omit
            bias_AA: Amino acid bias string
            bias_AA_per_residue: Per-residue bias (JSON string)
            omit_AA_per_residue: Per-residue omit (JSON string)
            job_name: Optional job name

        Returns:
            PokemonJobResult

        Example:
            with open("/tmp/structure.pdb", "r") as f:
                pdb_content = f.read()
            job = client.pokemon.proteinmpnn(
                output_vault_path="/MyProject/results",
                pdb_data=pdb_content,
                numSequences=5
            )
            print(job)
        """
        # Build params exactly matching job_request structure
        params: Dict[str, Any] = {
            "job_type": "proteinmpnn",
            "pdb_data": pdb_data,
            "designedResidues": designedResidues or {},
            "numSequences": numSequences,
            "temperature": temperature,
            "noiseLevel": noiseLevel,
            "omitAAs": omitAAs,
            "bias_AA": bias_AA,
            "bias_AA_per_residue": bias_AA_per_residue,
            "omit_AA_per_residue": omit_AA_per_residue,
        }

        return self._execute_tool("proteinmpnn", output_vault_path, params, job_name)

    # ============================================================================
    # Boltz2
    # ============================================================================

    def boltz2(
        self,
        output_vault_path: str,
        *,
        proteins: Optional[List[Dict[str, Any]]] = None,
        rnas: Optional[List[Dict[str, Any]]] = None,
        dnas: Optional[List[Dict[str, Any]]] = None,
        ligands: Optional[List[Dict[str, Any]]] = None,
        modifications: Optional[List[Dict[str, Any]]] = None,
        predict_affinity: bool = False,
        binder_chain: Optional[str] = None,
        num_samples: int = 5,
        num_recycles: int = 3,
        step_scale: float = 1.638,
        seed: int = 20,
        output_type: str = "pdb",
        version: str = "2.1.1",
        bonds: Optional[List[Dict[str, Any]]] = None,
        pocket_restraints: Optional[List[Dict[str, Any]]] = None,
        contact_restraints: Optional[List[Dict[str, Any]]] = None,
        job_name: Optional[str] = None,
    ) -> PokemonJobResult:
        """
        Run a Boltz2 structure prediction job.

        Args:
            output_vault_path: Vault path where results will be stored
            proteins: List of protein sequences (can include ids, cyclic, msa_file)
            rnas: List of RNA sequences
            dnas: List of DNA sequences
            ligands: List of ligands (input_type, smiles/ccd, cyclic, ids)
            modifications: List of modifications
            predict_affinity: Whether to predict binding affinity
            binder_chain: Chain ID for affinity prediction
            num_samples: Number of samples
            num_recycles: Number of recycles
            step_scale: Step scale factor
            seed: Random seed
            output_type: Output format ("pdb" or "mmcif")
            version: Boltz2 version
            bonds: List of bond constraints
            pocket_restraints: List of pocket restraint constraints
            contact_restraints: List of contact restraint constraints
            job_name: Optional job name

        Returns:
            PokemonJobResult

        Example:
            job = client.pokemon.boltz2(
                output_vault_path="/MyProject/results",
                proteins=[{"sequence": "MVLSPADKTNVK..."}],
                seed=42
            )
            print(job)
        """
        params: Dict[str, Any] = {
            "job_type": "boltz2",
            "numSamples": num_samples,
            "numRecycles": num_recycles,
            "stepScale": step_scale,
            "seed": seed,
            "outputType": output_type,
            "version": version,
        }

        if proteins:
            # Handle MSA files if present
            processed_proteins = []
            for p in proteins:
                p_copy = p.copy()
                if "msa_file" in p_copy and isinstance(p_copy["msa_file"], str):
                    p_copy["msa_file"] = self._read_file_content(p_copy["msa_file"])
                processed_proteins.append(p_copy)
            params["proteins"] = processed_proteins

        if rnas:
            processed_rnas = []
            for r in rnas:
                r_copy = r.copy()
                if "msa_file" in r_copy and isinstance(r_copy["msa_file"], str):
                    r_copy["msa_file"] = self._read_file_content(r_copy["msa_file"])
                processed_rnas.append(r_copy)
            params["rnas"] = processed_rnas

        if dnas:
            processed_dnas = []
            for d in dnas:
                d_copy = d.copy()
                if "msa_file" in d_copy and isinstance(d_copy["msa_file"], str):
                    d_copy["msa_file"] = self._read_file_content(d_copy["msa_file"])
                processed_dnas.append(d_copy)
            params["dnas"] = processed_dnas

        if ligands:
            params["ligands"] = ligands
        if modifications:
            params["modifications"] = modifications

        params["predictAffinity"] = predict_affinity
        if binder_chain:
            params["binderChain"] = binder_chain

        if bonds:
            params["bonds"] = bonds
        if pocket_restraints:
            params["pocketRestraints"] = pocket_restraints
        if contact_restraints:
            params["contactRestraints"] = contact_restraints

        return self._execute_tool("boltz2", output_vault_path, params, job_name)
