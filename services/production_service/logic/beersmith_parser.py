"""
BeerSmith Parser - Parse .bsmx XML files to Recipe model.

Supports BeerSmith 3 format (.bsmx).
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from models.recipe import Recipe


class BeerSmithParser:
    """
    Parse BeerSmith XML files (.bsmx) to Recipe objects.
    
    BeerSmith XML Structure (simplified):
    ```xml
    <Recipes>
      <Recipe>
        <F_R_NAME>American IPA</F_R_NAME>
        <F_R_BATCH_SIZE>20.0</F_R_BATCH_SIZE>
        <F_R_STYLE_NAME>American IPA</F_R_STYLE_NAME>
        <Ingredients>
          <Grain>
            <F_G_NAME>Pale Malt, Maris Otter</F_G_NAME>
            <F_G_AMOUNT>5.0</F_G_AMOUNT>
            <F_G_COLOR>3.0</F_G_COLOR>
          </Grain>
          <Hops>
            <F_H_NAME>Cascade</F_H_NAME>
            <F_H_AMOUNT>0.050</F_H_AMOUNT>
            <F_H_TIME>60.0</F_H_TIME>
          </Hops>
        </Ingredients>
      </Recipe>
    </Recipes>
    ```
    """
    
    @staticmethod
    def parse_file(file_path: str) -> Recipe:
        """
        Parse .bsmx file to Recipe object.
        
        Args:
            file_path: Path to .bsmx file
            
        Returns:
            Recipe object with parsed data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ET.ParseError: If XML is invalid
            ValueError: If required fields missing
        """
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Navigate to recipe (usually first Recipe tag)
        recipe_elem = root.find('.//Recipe')
        if recipe_elem is None:
            raise ValueError("No Recipe element found in XML")
        
        # Parse basic metadata
        name = BeerSmithParser._get_text(recipe_elem, 'F_R_NAME', required=True)
        style = BeerSmithParser._get_text(recipe_elem, 'F_R_STYLE_NAME', default='Unknown')
        brewer = BeerSmithParser._get_text(recipe_elem, 'F_R_BREWER', default='Desert Brew')
        batch_size = BeerSmithParser._get_float(recipe_elem, 'F_R_BATCH_SIZE', required=True)
        
        # Parse ingredients
        fermentables = BeerSmithParser._parse_fermentables(recipe_elem)
        hops = BeerSmithParser._parse_hops(recipe_elem)
        yeast = BeerSmithParser._parse_yeast(recipe_elem)
        
        # Parse calculated values
        expected_og = BeerSmithParser._get_float(recipe_elem, 'F_R_OG')
        expected_fg = BeerSmithParser._get_float(recipe_elem, 'F_R_FG')
        expected_abv = BeerSmithParser._get_float(recipe_elem, 'F_R_ABV')
        ibu = BeerSmithParser._get_float(recipe_elem, 'F_R_IBU')
        color_srm = BeerSmithParser._get_float(recipe_elem, 'F_R_COLOR')
        efficiency = BeerSmithParser._get_float(recipe_elem, 'F_R_EFFICIENCY', default=75.0)
        
        # Parse notes
        notes = BeerSmithParser._get_text(recipe_elem, 'F_R_NOTES', default='')
        
        # Create Recipe object
        recipe = Recipe(
            name=name,
            style=style,
            brewer=brewer,
            batch_size_liters=batch_size,
            fermentables=fermentables,
            hops=hops,
            yeast=yeast,
            expected_og=expected_og,
            expected_fg=expected_fg,
            expected_abv=expected_abv,
            ibu=ibu,
            color_srm=color_srm,
            brewhouse_efficiency=efficiency,
            notes=notes,
            bsmx_file_path=file_path,
            bsmx_file_name=file_path.split('/')[-1]
        )
        
        return recipe
    
    @staticmethod
    def _parse_fermentables(recipe_elem: ET.Element) -> List[Dict]:
        """Parse fermentables (malts) from XML."""
        fermentables = []
        
        grains = recipe_elem.findall('.//Grain')
        for grain in grains:
            name = BeerSmithParser._get_text(grain, 'F_G_NAME')
            if not name:
                continue
            
            amount_kg = BeerSmithParser._get_float(grain, 'F_G_AMOUNT', default=0.0)
            color_srm = BeerSmithParser._get_float(grain, 'F_G_COLOR', default=0.0)
            grain_type = BeerSmithParser._get_text(grain, 'F_G_TYPE', default='Grain')
            
            fermentables.append({
                'name': name,
                'amount_kg': amount_kg,
                'color_srm': color_srm,
                'type': grain_type
            })
        
        return fermentables
    
    @staticmethod
    def _parse_hops(recipe_elem: ET.Element) -> List[Dict]:
        """Parse hops from XML."""
        hops_list = []
        
        hops = recipe_elem.findall('.//Hops')
        for hop in hops:
            name = BeerSmithParser._get_text(hop, 'F_H_NAME')
            if not name:
                continue
            
            # BeerSmith stores hops in kg, convert to grams
            amount_kg = BeerSmithParser._get_float(hop, 'F_H_AMOUNT', default=0.0)
            amount_g = amount_kg * 1000
            
            time_min = BeerSmithParser._get_float(hop, 'F_H_BOIL_TIME', default=60.0)
            use = BeerSmithParser._get_text(hop, 'F_H_USE', default='Boil')
            alpha_acid = BeerSmithParser._get_float(hop, 'F_H_ALPHA', default=0.0)
            
            hops_list.append({
                'name': name,
                'amount_g': amount_g,
                'time_min': time_min,
                'use': use,
                'alpha_acid': alpha_acid
            })
        
        return hops_list
    
    @staticmethod
    def _parse_yeast(recipe_elem: ET.Element) -> List[Dict]:
        """Parse yeast from XML."""
        yeast_list = []
        
        yeasts = recipe_elem.findall('.//Yeast')
        for yeast in yeasts:
            name = BeerSmithParser._get_text(yeast, 'F_Y_NAME')
            if not name:
                continue
            
            lab = BeerSmithParser._get_text(yeast, 'F_Y_LAB', default='')
            product_id = BeerSmithParser._get_text(yeast, 'F_Y_PRODUCT_ID', default='')
            yeast_type = BeerSmithParser._get_text(yeast, 'F_Y_TYPE', default='Ale')
            
            yeast_list.append({
                'name': name,
                'lab': lab,
                'product_id': product_id,
                'type': yeast_type
            })
        
        return yeast_list
    
    @staticmethod
    def _get_text(elem: ET.Element, tag: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
        """Get text content from XML element."""
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        if required:
            raise ValueError(f"Required field '{tag}' not found")
        return default
    
    @staticmethod
    def _get_float(elem: ET.Element, tag: str, default: Optional[float] = None, required: bool = False) -> Optional[float]:
        """Get float value from XML element."""
        text = BeerSmithParser._get_text(elem, tag, required=required)
        if text is None:
            return default
        try:
            return float(text)
        except ValueError:
            if required:
                raise ValueError(f"Field '{tag}' must be a number")
            return default
