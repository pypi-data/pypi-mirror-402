# -*- coding: utf-8 -*-
"""
Multi-scale mapping of PRIMAP data into an MRIO table.

Created on Wed May 11 12:57:54 2022
@author: beaufils
"""

import os
import io
import csv
import pandas as pd
import numpy as np
from mrio_toolbox import MRIO
import logging as log

log.getLogger(__name__)

#Paths collection
package_directory = os.path.dirname(os.path.abspath(__file__))
mrio_path = os.path.join(package_directory,"MRIO")
primap_path = os.path.join(package_directory,'PRIMAP')
mapping_path = os.path.join(package_directory,'mappings')
extension_path = os.path.join(mrio_path,"eora26","formatted")
crf_version = '2021_1'
crf_name = 'Guetschow-et-al-2021-PRIMAP-crf_2021-v1'
hist_version='2.4.2'
hist_name = 'Guetschow-et-al-2023a-PRIMAP-hist_v2.4.2_final_09-Mar-2023'

#Global Warming Potentials (GWPs) for computing the Kyoto GHG basket
#Current version: Fourth Assessment Report (AR4)
gwp = {
    "CO2" : 1,
    "CH4" : 25,
    "N2O" : 298,
    "HFCS (AR4GWP100)" : 1,
    "PFCS (AR4GWP100)" : 1,
    "SF6" : 22800,
    }

def multi_scale_mapping(
        mrio,
         mapping_file='template_crf_mapping', year=2015, emissions_year = "same", 
         mapping_extension=".csv",
         table='icio2021',
         primap_path = primap_path,
         mapping_path = mapping_path,
         entities =['CO2'], kyoto_basket = False,
         crf_version = crf_version, crf_name = crf_name,
         hist_version = hist_version, hist_name = hist_name,
         categories_output=['M.0.EL'],min_sources=5,
         **kwargs):
    """
    Maps PRIMAP data into an MRIO.
    Produces satellite matrices for GHGs listed in 'entities'.

    Parameters
    ----------
    mapping_file : str, optional
        Name of the mapping file to use.
    year : int, optional
        Data year to use.
        Make sure that data are available for that year 
        in both PRIMAP and the MRIOT.
    emissions_year : int or "same", optional
        Year to use as a source for emission data.
        If "same", taken as the "year" variable.
    mapping_extension : str
        Extension under which the mapping table is saved.
        Currently supported: excel (.xslx) and csv (.csv)
    primap_path : path-like, optional
         Path to the folder containing the Primap data.
    mapping_path : path-like, optional
        Path to the folder containing the mapping instructions
    entities : list of strings, optional
        List of GHGs to map. 
        Refer to the PRIMAP-hist file for the GHGs available.
        The default is CO2.
    kyoto_basket : bool, optional
        Whether to include a custom estimation of global GHG emissions
        (in kt/CO2e) based on the global warming potential.
    crf_version : str, optional
        Version of the PRIMAP-crf database.
    crf_name : str, optional
        Name of the PRIMAP-crf file.
    hist_version : str
        Version of the  PRIMAP-hist database.
    hist_name : str, optional
        Name of the PRIMAP-hist file.
    categories_output : str, optional
        List of crf categories to return.
        The default is M.0.EL, i.e. total emissions excluding land use.
        If "all", all crf categories are returned.
    min_sources : int, optional
        Minimal number of sources available in Primap crf to compute 
        a world average intensity coefficients.
        The default is 10.
    include_emission_version : bool
        Whether to include crf and hist data code to the file name
        
    Returns
    -------
    None. Files are saved directly in the extension_path folder.

    """
    log.info(f"Map emissions for {table} in {year}")
    emissions_year = kwargs.get("emissions_year", year)

    countries_name = kwargs.get("countries","countries")
    sectors_name = kwargs.get("sectors","sectors")

    log.info("Loading MRIO data")
    go,countries,sectors = get_go(mrio,
                                  countries_name,
                                  sectors_name,
                                  kwargs.get("final_demand","y"),
                                  kwargs.get("inter_industry","t"))
    nsectors = len(sectors) - 1 #Excludes final demand from sectors count
    log.info("Done")
    
    log.info("Load mapping and PRIMAP crf")
    cat_crf,mapping,crf_parents,crf_childs = \
        load_mapping(mapping_path,mapping_file,sectors,mapping_extension)
    crf = load_primap(primap_path, crf_version, crf_name,emissions_year, 
                      countries, cat_crf, entities, mode='crf')
    log.info("Done")
    #Compute the intensity factors for each emission category and each GHG
    intensity,sources_intensity = \
        intensity_factor(crf,mapping,cat_crf,countries,go,entities,
                         nsectors, min_sources)

    #Order crf data into a 3D file, 
    #with information available for each GHG/country/category
    crf = order_primap(crf, countries,cat_crf,entities,mode='crf')
    #Create a coupled 'crf' file for storing the state of knowledge of the data
    computed = np.copy(crf)
    ratio = np.zeros([len(countries),len(entities),len(cat_crf)])
    ratio[crf!=0] = 1   #Mark known values as sourced inputs
    
    #First step: extrapolation using crf intensity factors
    for country_id in range(len(countries)):
        for entity_id in range(len(entities)):
            data = np.copy(crf[country_id,entity_id])    
            #Extract data for the corresponding country/gas from the crf table
            extract_i = intensity[entity_id]    
            #Extract intensity factors for the corresponding gas
            goi = np.concatenate((go[0][
                country_id*(len(sectors)-1):(country_id+1)*(len(sectors)-1)],
                [go[1][country_id]]))  
            #Extract and aggregate national gross output and final demand 
            #Incorporate estimations in 'computed' file, 
            #track changes (previously known/aggregated/unknown) 
            #in the 'ratio' file
            data,ratio[country_id,entity_id] = \
                aggregate(data,extract_i,goi,ratio[country_id,entity_id],
                          crf_parents,crf_childs,mapping)
            computed[country_id,entity_id],ratio[country_id,entity_id] = \
                down_adjustment(data,ratio[country_id,entity_id],
                                crf_parents,crf_childs)
    check_consistency(computed,crf,ratio,crf_parents,crf_childs)
    log.info('First emission tree estimated from Primap crf')
    
    #Second step: integrate Primp-hist data
    hist = load_primap(primap_path, hist_version, hist_name, emissions_year, 
                       countries, cat_crf, entities, mode='hist')
    hist = order_primap(hist,countries,cat_crf,entities,mode='hist')
    computed[hist!=0] = hist[hist!=0]
    ratio[hist!=0] = 1
    for country_id in range(len(countries)):
        for entity_id in range(len(entities)):
            data = np.copy(hist[country_id,entity_id])
            #Set total emissions to 0 for countries not covered in primap_hist
            computed[country_id,entity_id,0] = hist[country_id,entity_id,0]
            computed[country_id,entity_id],ratio[country_id,entity_id] =\
                down_adjustment(computed[country_id,entity_id],
                                ratio[country_id,entity_id],
                                crf_parents,crf_childs)
    check_consistency(computed,hist,ratio,crf_parents,crf_childs)
    log.info('Emission tree adjusted to Primap hist')
    
    if kyoto_basket:
        log.info("Estimating Kyoto GHG basket")
        computed,ratio,entities = kyoto_allocation(computed,ratio,entities)
        intensity = np.insert(intensity, -1, np.zeros(np.shape(intensity[0])),
                              axis=0)
        sources_intensity = np.insert(sources_intensity, -1, 
                                      np.zeros(np.shape(sources_intensity[0])),
                                      axis=0)
    
    if categories_output == "all":
        cat_output = [i for i in range(len(cat_crf))]
    else:
        cat_output = [cat_crf.index(i) for i in categories_output]
    labels_cat = [cat_crf[cat] for cat in cat_output]
    qt,qy = to_mrio(computed,len(countries),crf_parents,crf_childs,
                    mapping,entities,go,len(sectors)-1,cat_output)
    intensity = pd.DataFrame(data=np.transpose(intensity),
                             columns=entities,index=cat_crf)
    sources_intensity = pd.DataFrame(data = np.transpose(sources_intensity),
                                     columns=entities,index=cat_crf)
    
    mrio.add_dimensions({
        "GHG" : entities,
        "Emission categories" : labels_cat,
    })
    mrio.parts["qy"] = mrio.new_part(
        name="qy", data=qy,
        dimensions = [["GHG","Emission categories"],[countries_name]]
    )
    mrio.parts["qt"] = mrio.new_part(
        name="qt", data=qt,
        dimensions = [["GHG","Emission categories"],[countries_name,sectors_name]]
    )

#LOADERS

def get_go(mrio,
           countries,
           sectors,
           final_demand,
           inter_industry):
    """
    Extracts the gross output and total final demand per sector
    from an MRIO table as well as the countries and sectors lists.

    Parameters
    ----------
    mrio : mrio instance
    countries, sectors, final_demand, inter_industry : str
        Aliases for the MRIO table elements
        Default: countries, sectors, y, t

    Returns
    -------
    list of list of floats
        First list holds gross output per sector.
        Second list holds final demand per sector (domestic + foreign).
    """
    countries = mrio.labels[countries].copy()
    sectors = mrio.labels[sectors].copy()
    sectors.append("Final demand") #For allocating emission from final use
    y = mrio.parts[final_demand]
    t = mrio.parts[inter_industry]
    fd_sum = y.sum(axis=0)
    x = t.sum(axis=1) + y.sum(axis=1)
    x.data[x.data==0] = 1 #Avoid division by 0
    return [x.data,fd_sum.data],countries,sectors

## Mapping loader

def load_mapping(path,name,sectors, extension,
                 exclude_LULUCF = True):
    """
    Load the mapping between Primap emissions categories and MRIO sectors.
    The variable 'closed_branch' tracks if subcategories should be explored.
    It is set to false once an end-category is defined, until the algorithm
    explores a new branch.

    Parameters
    ----------
    path : path-like
        Path to the folder storing the mapping file.
    name : str
        Name of the mapping description file.
    sectors : list of str
        List of economic sectors.
    extension : str
        Extension under which the mapping table is saved.
        Currently supported: excel (.xslx) and csv (.csv)
    exclude_LULUCF : Boolean, optional
        Whether to exclude Land use related emissions. The default is True.
        The grand total per country is set to 'M.0.EL' instead of '0'.

    Returns
    -------
    cat : list of strings
        Label of IPCC categories.
    mapping : list of ints
        Index of corresponding EORA sector.
    parents : list of ints
        List of index of parent categories.
    childs : list of list of ints
        Lists of indexes of children categories.
        Index of list of children refers to index in parents' list.

    """
    if extension == ".xslx":
        source = pd.read_excel(os.path.join(path,
                                   '{}.xlsx'.format(name))).to_numpy(dtype=str)
    elif extension == ".csv":
        source = pd.read_csv(os.path.join(path,
                                          '{}.csv'.format(name))
                             ).to_numpy(dtype=str)
    else: 
        raise ValueError(f"Unsupported mapping extension: {extension}")
    
    #List all end-categories
    end_categories,id_end = list(),list()
    for i,row in enumerate(source):
        if row[2]!="nan":
            end_categories.append(row[0])
            id_end.append(i)
    
    categories = ["M.0.EL"]
    parents = [0]
    children = [[]]
    mapping = [[]]

    #Select the categories to include in the tree
    for category in end_categories:
        split = category.split('.')
        current = str()
        for part in split:
            if len(current) == 0:
                current = part
            else:
                current = ".".join([current,part])
            if current not in categories:
                categories.append(current)
    
    #Create the tree
    for i,category in enumerate(categories):
        if category == "M.0.EL":
            #Split the total emission category
            continue
        if len(category) == 1:
            #If the category is a direct child of M.0.EL
            children[0].append(i)
        else:
            #If the category is a child of another category
            split = category.split('.')
            parent = ".".join(split[:-1])
            id_parent = categories.index(parent)
            if id_parent not in parents:
                children.append([])
                parents.append(id_parent)
            children[parents.index(id_parent)].append(i)
        tomap = []
        if category in end_categories:
            row = source[id_end[end_categories.index(category)]]
            j=2
            while j<len(row) and row[j]!='nan':
                tomap.append(sectors.index(str(row[j].strip())))
                j+=1
        mapping.append(tomap)

    if exclude_LULUCF:
        categories[categories.index('3')] = 'M.AG'
    
    return categories, mapping, parents, children
    
## Primap loader

def load_primap(path,version,name,year,countries_list,cat_crf,entities,
                mode='crf'):
    """
    Extract data from a PRIMAP database for a given year and given GHGs.

    Parameters
    ----------
    path : path-like
        Path to the PRIMAP data.
    version : str
        Version of the PRIMAP data.
    name : str
        Name of the PRIMAP file
    year : int
        Year data to consider.
    countries : list of strings
        List of A3 country codes for countries covered in the MRIOT.
    cat_crf : list of strings
        Name of emission categories to extract.
    entities : list of strings
        GHGs to extract.
    mode : 'crf' or 'hist'
        Type of database to load.
        Selection criterions are different depending on the table to laod.

    Returns
    -------
    list of arrays
        First array holds labels (country,category,GHG).
        Second array holds values.
    """
    file = io.open(os.path.join(path,'{}_{}'.format(mode,version),
                                '{}.csv'.format(name)),
                       "r",encoding = 'utf-8-sig')
    reader = csv.reader(file, delimiter = ',')
    labels = []
    values = []
    countries = countries_list.copy()
    if "ROW" in countries and mode == 'hist':
        #If extracts from hist, includes world emissions to deduce ROW
        countries.append('EARTH')
    for row in reader:
        if mode == 'crf':
            if (row[3] in countries and row[6] in cat_crf and
                row[4] in entities and row[year-1979] != ''):
                labels.append([row[3],row[6],row[4]])
                values.append(row[year-1979])
        else:
            if (row[1] == 'HISTTP' and row[2] in countries and 
                row[5] in cat_crf and row[3] in entities and 
                row[year-1744]!=''):
                labels.append([row[2],row[5],row[3]])
                values.append(row[year-1744]) 
    return [np.array(labels,dtype=str),np.array(values,dtype=float)]

def order_primap(data, countries_list,cat_crf,entities, mode ='crf'):
    """
    Order data from PRIMAP into a 3D table (GHG x country x category).
    Uncovered categories/countries are set to 0.
    If a rest of the world region is defined, its emissions are set
    as the difference between the world emissions and the emissions
    assigned to other countries.

    Parameters
    ----------
    data : list of lists
        PRIMAP-crf base data (as returned by load_crf)
    countries : list of strings
        List of country A3 codes from the MRIOT.
    cat_crf : list of strings
        List of emission categories.
    entities : list of strings
        GHG covered.
    mode : 'crf' or 'hist'
        Type of database to format.
        If hist, row emissions are deducted from world emissions.

    Returns
    -------
    output : 3D array
        Table of sourced emissions per GHG, country and emission category.
    """
    countries = countries_list.copy()
    if 'ROW' in countries and mode =='hist':
        countries.append('EARTH')
    output = np.zeros([len(countries),len(entities),len(cat_crf)])
    for i in range(len(data[0])):
        country = countries.index(data[0][i][0])
        entity = entities.index(data[0][i][2])
        category = cat_crf.index(data[0][i][1])
        output[country,entity,category] = data[1][i]
        
    if 'ROW' in countries and mode=='hist':
        #Deduce emissions from the rest of the world
        earth = output[-1,:,:]
        output = np.delete(output,-1,0)
        row = countries.index('ROW')
        world = np.sum(output,axis=0)
        for j in range(len(entities)):
            for k in range(len(cat_crf)):
                #Round world emissions to 3 significant digits
                #To avoid rounding errors
                world[j,k] = float('%.3g' %world[j,k])
        residual = earth - world
        neg_row = np.where(residual<0)
        for i in range(len(neg_row[0])):
            log.info("Negative estimation for row {} emissions in IPCC {}".format(
                entities[neg_row[0][i]],cat_crf[neg_row[1][i]]))
            log.info("Found {} cumulated emissions instead of {}".format(
                world[neg_row[0][i],neg_row[1][i]],
                earth[neg_row[0][i],neg_row[1][i]]))
            log.info("Overwrite row emissions to 0.")
            residual[neg_row[0][i],neg_row[1][i]] = 0
        output[row,:,:] = residual
    #assert np.sum(output<0) == 0        
    return output

# Operations

def intensity_factor(crf,concordance,cat_crf,countries_list,go,entities,
                     nsectors,min_sources=10):
    """
    Computes average emissions intensity coefficient for end-categories.
    End-categories are defined are emission categories associated with 
    one or several economic sectors.
    Emission intensity coefficients are computed using PRIMAP-crf emission data
    and WIOD economic output values.

    Parameters
    ----------
    crf : list of arrays
        Data from PRIMAP-crf, as extracted from load_crf.
    concordance : list of list of ints
        Mapping table from emission categories to economic sectors.
    cat_crf : list of strings
        List of IPCC emission categories labels.
    countries : list of string
        List of A3 country codes for countries covered in WIOD.
    go : list of float
        Economic output per sector.
    min_sources : int, optional
        Minimal number of sources to create an intensity coefficient. 
        The default is 0.

    Returns
    -------
    intensity : 2D matrix
        Emission intensity coefficient for each GHG and each category.
    sources : 2D matrix
        Number of countries used for determining the emission intensity coeff.

    """
    countries = countries_list.copy()
    intensity = np.zeros([len(entities),len(cat_crf)])
    sources = np.zeros([len(entities),len(cat_crf)])
    for rowid,entity in enumerate(entities):
        for colid, category in enumerate(cat_crf):
            countries_name = []
            emissions = 0
            source = 0
            if concordance[colid] != []: 
                #If the category is associated with some economic sectors
                indices = [(label[1] == category and label[2] == entity)
                           for label in crf[0]] 
                #List all countries for which data is reported
                source = np.sum(indices)
                emissions = np.sum(crf[1][indices])
                countries_name = crf[0][indices][:,0]
                sources[rowid,colid] = source
                if source>min_sources:  
                    #If enough sources are available, 
                    #computes the average factor of the category
                    index_countries = []
                    production = 0
                    for country in countries_name:
                        index_countries.append(countries.index(country))
                    for sector in concordance[colid]:
                        if sector == nsectors:
                            production += \
                                np.sum([go[1][i] for i in index_countries])
                        else:
                            production += np.sum(
                                [go[0][i*nsectors + sector] 
                                 for i in index_countries])
                    intensity[rowid,colid] = emissions/production
    return intensity,sources

def aggregate(data,intensity,go,known,crf_parents,crf_childs,concordance):
    """
    Bottom up consolidation of the emission tree.
    Successively estimates emissions in the emission tree,
    starting from end-categories up to total emissions.
    Uses emission intensity coeffs when no emission data are reported.

    Parameters
    ----------
    data : 1D array
        IPCC emission data from PRIMAP-crf for a country/GHG.
    intensity : 1D array
        Intensity coefficient array for the corresponding GHG.
    go : 1D array
        Economic output per sector.
    known : 1D array
        Source status associated with source data.
            - 0 is unknown
            - 1 is known from PRIMAP-crf   
            - 2 is estimated
            
    crf_parents : list of ints
        Indices of parent categories.
    crf_childs : list of list of ints
        List of children categories per parent.
    concordance : list of ints
        Mapping of emission categories with economic sectors.

    Returns
    -------
    data : 1D array
        aggregated emission array.
    known : 1D array
        Updated information on data source.
    """
    aggregation = np.copy(data)
    for i in range(len(crf_parents),0,-1):
        #Identify parents and children categories
        parent = crf_parents[i-1]
        childs_id = crf_childs[i-1]
        for children in childs_id:
            if known[children] == 0 and concordance[children] != []:
                #If a children is null and is an end-category, 
                #estimate is computed using the intensity factor
                for sector in concordance[children]:
                    aggregation[children] += \
                        intensity[children]*go[sector]
                known[children] = 2 #Children is marked as aggregated
        if known[parent] == 0:
            #If the parent is unknown, 
            #child estimation are aggregated to form a parent estimation
            aggregation[parent] = np.sum([aggregation[child] for child in childs_id])
            known[parent] = 2
    return aggregation,known

def down_adjustment(data,known,crf_parents,crf_childs):
    """
    Top-down adjustment of the emission tree.
    Ensures consistence between aggregated data and sub-categories.
    Adjusts estimated coefficients.
    If unconsistences in sourced data, known sub-categories are adjusted
    and estimated sub-categories are set to 0.
    
    Parameters
    ----------
    data : 1D numpy array
        Emissions values estimated for the emission categories 
        of the corresponding gas and country.
    known : 1D numpy array
        State of knowledge of the available information:
            - 0 is no information
            - 1 is original information
            - 2 is estimated value.
            
    crf_parents : list of ints
        list of aggregated emission categories.
    crf_childs : list of list of ints
        List of list of sub-categories associated with the parent categories.

    Returns
    -------
    data : 1D numpy array
        Updated emission values.
    known : 1D numpy array
        Updated information on the estimations:
            2 = source data
            x (float) = adjustment ratio
            -1 = has been set to 0 because children exceeded parents

    """
    for i in range(len(crf_parents)):   
        parent = crf_parents[i]
        childs = crf_childs[i]
        current_multiplier = known[parent]
        #When splitting data between children, known children left untouched
        sure = 0
        unsure = 0
        tobalance = []
        for child in childs:
            if known[child] == 1:
                sure += data[child] #Sums up the values of the sourced childs
            else:
                tobalance.append(child)
                unsure += data[child]   
                #Sums up the values of the estimated childs
        tomake = data[parent] - sure 
        
        #Computes the emissions to allocate between the estimated childs
        for kid in tobalance:
            if unsure > 0 and tomake > 0:  
                #If residual is positive, 
                #proportionally allocate extra emissions to estimated children
                data[kid] = data[kid]*tomake/unsure
                known[kid] = current_multiplier*tomake/unsure 
                #Support array marks the adjustment coefficient
            if tomake <= 0:  
                #If residual is negative, estimated emissions are assumed null
                data[kid] = 0
                #Support array marks that extrapolation is not possible 
                #because all emissions are already allocated
                known[kid] = 0
        children = [data[children] for children in childs]
        made = np.sum(children)
        if made != data[parent]: 
            #If total of children is still different to parent, 
            #sourced childs are proportionally adjusted
            for children in childs:
                if made == 0:
                    #If parent is reported but all children are null
                    #Emissions are allocated proportionally to childs
                    data[children] = data[parent]/len(childs)
                    known[children] = 2
                else:
                    data[children] = data[children]*data[parent]/made
                    known[children] = current_multiplier*data[parent]/made 
                    #Support array registers the adjustment coefficient
        children = [data[children] for children in childs]
        assert np.isclose(np.sum(children),data[parent])
    return data, known

def kyoto_allocation(data,ratio,entities):
    """
    Computes the total GHG emissions using the GWP defined in preambles.
    Replaces the Kyoto GHG estimated from the PRIMAP Kyoto estimates.

    Parameters
    ----------
    data : 3D array
        Table of sourced emissions per GHG, country and emission category.
    ratio : 3D array
        Table of adjustment coefficents per GHG, country and emission category.
    entities : list of str
        List of GHG allocated.

    Returns
    -------
    data : 3D array
        Table of sourced emissions per emission category GHG and country,
        with estimated Kyoto GHG basket.
    ratio : 3D array
        Table of adjustment coefficents per GHG, country and emission category.
        All coefficients for the Kyoto basket are set to 2 (estimated).

    """
    
    kyoto = np.zeros((len(data),1,len(data[0,0])))
    kratio = np.zeros((len(data),1,len(data[0,0])))
    for i,entity in enumerate(entities):
        if entity in gwp:
            kyoto[:,0,:] += data[:,i,:]*gwp[entity]
    kratio[:,:,:] = 2
    data = np.concatenate((data, kyoto), axis=1)
    kratio = np.concatenate((ratio, kratio),axis=1)
    entities.append("Kyoto GHG AR4")
    return data,ratio,entities


# Annex functions

def check_consistency(test,source,known,crf_parents,crf_childs):
    """
    Test the consistency of the emission tree.
    Ensure that the sum of each children category equals its parent.

    Parameters
    ----------
    test : 3D array
        Emission table to assess.
    primap : 
    crf_parents : list of ints
        list of aggregated emission categories.
    crf_childs : list of list of ints
        List of list of sub-categories associated with the parent categories.

    Returns
    -------
    None. Asserts that sum of children equals parent for every pair.
    """
    for i in range(len(test)):
        for j in range(len(test[0])):
            for k in range(len(crf_parents)):
                parent = test[i,j,crf_parents[k]]
                children = [test[i,j,child] for child in crf_childs[k]]
                children = np.sum(children)
                assert np.isclose(parent,children)

def to_mrio(data,countries,crf_parents,crf_childs,mapping,entities,go,
            sectors=56,categories=[0]):
    """
    Maps emission tables into MRIO economic sectors.
    If an emission category is mapped to multiple economic sectors,
    emissions are allocated proportionally to the output of each sector.

    Parameters
    ----------
    data : 3D array
        Emission table.
    countries : int
        Number of countries covered.
    crf_parents : list of ints
        list of aggregated emission categories.
    crf_childs : list of list of ints
        List of list of sub-categories associated with the parent categories.
    mapping : list of ints
        Concordance between WIOD sectors and emission categories.
    entities : list of strings
        List of GHGs covered.
    go : list of float
        Economic output per sector.
    sectors : int, optional
        Economic sectors per country The default is 26.
    categories : list of ints, optional
        Emission categories to report. The default is [0].

    Returns
    -------
    qt : 2D array
       Emission matrix for intermediate sectors.
    qy : 2D array
        Emission matrix for final demand.

    """
    n = len(categories)
    e = len(entities)
    qt = np.zeros((e*n,countries*sectors))
    qy = np.zeros((e*n,countries))
    
    
    selection = [look_for_children(i,crf_parents,crf_childs,[]) 
                 for i in categories]
    for entity in range(e):
        for country in range(countries):
            for i,cat in enumerate(selection):
                count = 0
                ref = data[country,entity,categories[i]]
                for item in cat:
                    count += data[country,entity,item]
                    subref = data[country,entity,item]
                    subcount = 0
                    production = 0
                    #Allocate emissions to sectors associated to end categories
                    for sector in mapping[item]:
                        #Aggregate production from associated sectors
                        if sector != sectors:
                            production += go[0][country*sectors+sector]
                        elif sector == sectors:
                            production += go[1][country]
                    for sector in mapping[item]:
                        #Allocate emissions proportionally to the sector size
                        if sector != sectors and production !=0:
                            subcount += data[country,entity,item]*\
                            go[0][country*sectors+sector]/production
                            qt[entity*n+i,country*sectors+sector] += \
                                data[country,entity,item]*\
                                go[0][country*sectors+sector]/production
                        elif sector == sectors and production !=0:
                            subcount += data[country,entity,item]*\
                                go[1][country]/production
                            qy[entity*n+i,country] += \
                                data[country,entity,item]*\
                                    go[1][country]/production
                    if production == 0 and data[country,entity,item]!=0:
                        #If the sector is null in the MRIO, emissions
                        #are allocated to the final demand
                        qy[entity*n+i,country] += data[country,entity,item]
                        subcount += data[country,entity,item]
                        log.info("Empty sector at index {} in country {}".format(
                            sector,country))
                        log.info("Allocating {} emissions to the final demand."\
                              .format(data[country,entity,item]))
                    assert np.isclose(subcount,subref)
                assert np.isclose(count,ref)
                #Check whether emissions reported match aggregated values
    return qt,qy

def look_for_children(category,parents,childs,output=[]):
    '''
    Recursive function to find all end-categories to include
    in the reporting of selected category.

    Parameters
    ----------
    category : int
        Emission category under investigation
    parents : list of ints
        list of aggregated emission categories.
    childs : list of list of ints
        List of list of sub-categories associated with the parent categories.
    output : list of ints
        Aggregated list of categories covered by the inital category called.

    Returns
    -------
    output: list of ints
        List of end-categories covered by the initial category called.

    '''
    if category not in parents:
        output.append(category)
    else:
        for child in childs[parents.index(category)]:
            output=look_for_children(child,parents,childs,output)
    return output