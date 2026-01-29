"""
Functions to build an MRIO object from GTAP data.
"""

import mrio_toolbox as mrio
import logging

log = logging.getLogger(__name__)

def transform_gtap(gtap):
    """
    Convert the gtap data into an MRIO object.

    Parameters
    ----------
    gtap : xarray Dataset
        Extracted gtap data
    """
    return mrio.MRIO(data=gtap)

def build_io(gtap):
    """
    Create the input-output table from the GTAP data

    This function treats GTAP data as is.
    It does not solve any imbalance and stays as close as possible
    to the raw dataset.

    The international trade block allocation follows 
    from the proportionality assumptions.
    Given the disagreement between import and export data,
    we average the two to get the bilateral trade shares.
    
    Parameters
    ----------
    gtap_data : MRIO object
        Direct extraction from the gtap data
    """
    if not isinstance(gtap,mrio.MRIO):
        gtap = transform_gtap(gtap)

    #We solve the disagreement between import and export data
    #by averaging the two
    log.info("Compute the trade shares")
    trade = (gtap.VXSB + gtap.VMSB)/2
    
    #There are some non-null elements in the diagonal of the trade matrix
    #These are statistical artefact from GTAP. We set them to zero.
    for country in gtap.REG:
        trade["all",country,country] = 0
    
    #Then, we normalize the trade shares
    imports = trade.sum(axis=1)
    imports.data[imports.data == 0] = 1
    shares = trade/imports.expand_dims(axis=1)
    #Shares is of shape (sectors,country of origin, country of destination)
    #Shares some to 1 for each sector and country of destination

    #Now, we create the inter-industry matrix
    log.info("Create the inter-industry matrix")
    log.info("Fill the diagonal blocks")
    T = gtap.new_part(name="t",dimensions=(("REG","COMM"),("REG","COMM")))

    log.info("Fill the off-diagonal blocks")
    for current in gtap.REG:
        #We create the inter-industry matrix within each country
        #We only need to fit VDFB into the diagonal blocks of the matrix
        T[(current,"all"),(current,"all")] = gtap.VDFB["all","all",current]
        for partner in gtap.REG:
            #We create the international trade block for each trade partner
            if partner != current:
                #We use the trade shares to split the sectoral imports 
                #by trade partner
                #This is known as the proportionality assumption
                #It means that the trade shares of a country in a given market
                #Does not depend on the sector buying it
                T[(partner,"all"),(current,"all")] = gtap.VMFB[
                    "all","all",current
                    ]*shares[
                    "all",partner,current
                    ]
    
    log.info("Create the final demand matrix")
    #We turn to the final demand matrix
    #First, we create the labels for the final demand categories
    gtap.labels["y_labs"] = ["Households","Government","Investment"]

    #Now, we create the final demand matrix
    Y = gtap.new_part(name="y",dimensions=(("REG","COMM"),("REG","y_labs")))

    #The process is similar to the inter-industry matrix,
    #but we have to loop over the final demand categories
    categories = {
        "Households":"P",
        "Government":"G",
        "Investment":"I"
    }
    for country in gtap.REG:
        for category in categories:
            #Fill the domestic use of domestic products
            Y[(country,"all"),(country,category)] = gtap.parts[
                f"VD{categories[category]}B"]["all",country]
            for partner in gtap.REG:
                if partner != country:
                    #Fill the imports from each trade partner
                    Y[(partner,"all"),(country,category)] = gtap.parts[
                        f"VM{categories[category]}B"
                        ]["all",country].data[:,None,:]*shares[
                        "all",partner,country
                    ].data

    #Finally, we create the value added matrix.
    #Our value added in basic prices encompasses the primary endowments,
    #margins and net taxes and subsidies.
    #Margins also include export taxes and subsidies,
    #as these do not abund the value added of the importing country.

    #Prepare the primary inputs / value added labels
    log.info("Create the value added matrix")
    va_labs = []
    for endowment in gtap.ENDW:
        va_labs.append(endowment)
    va_labs.append("margins")
    va_labs.append("net taxes and subsidies")
    gtap.labels["va_labs"] = va_labs

    #Create the value added matrix
    VA = gtap.new_part(name="va",dimensions=(("va_labs"),("REG","COMM")))

    #Reformat the va_labs
    log.info("Cast the va_labs")
    endowments = gtap.EVFB.reformat([["ENDW"],["ACTS","REG"]])
    endowments = endowments.swap_ax_levels(1,"ACTS","REG")
    VA[gtap.ENDW] = endowments

    #Aggregate the margins and export taxes and subsidies
    log.info("Aggregate margins and export taxes and subsidies")
    margins = gtap.VTWR.sum(-1).sum(0) + gtap.XTRV.sum(2)
    margins = margins.flatten()
    margins = margins.swap_ax_levels(0,"COMM","REG")
    VA[["margins"]] = margins

    #Get the net taxes and subsidies as the residual
    log.info("Derive net taxes and subsidies")
    output = T.sum(1) + Y.sum(1)
    VA[["net taxes and subsidies"]] = output - T.sum(0) - VA.sum(0)

    gtap_mrio = mrio.MRIO()
    gtap_mrio.metadata = gtap.metadata
    for part in [T,Y,VA]:
        gtap_mrio.add_part(part)

    gtap_mrio.rename_dimensions(
        ["REG","COMM"],
        ["countries","sectors"]
    )

    return gtap_mrio